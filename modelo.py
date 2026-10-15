"""Kaido A013: previsión, validación temporal y simulación FIFO reproducible.
Ejecutar: python modelo.py --n 1000 --seed 20261008
Solo requiere numpy y pandas. Todos los supuestos están en config.json.
"""
from pathlib import Path
import argparse, json, hashlib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
SEG = ['B','C','MD','SSUV','CSUV','MSUV','S']
CHANNELS = ['PARTICULARES','EMPRESAS_RENTING','ALQUILADORES']
EVENTS = ['incentivo_publico','adelanto_compras','caida_tras_adelanto','subida_iva']
ECON = {'PARTICULARES':['paro','confianza_consumidor','tipo_credito_consumo'],
        'EMPRESAS_RENTING':['paro','pib_var','indice_actividad'],
        'ALQUILADORES':['paro','viajeros_var']}

def read(name):
    return pd.read_csv(ROOT/'data'/name, keep_default_na=False, na_values=[''])

class Ridge:
    def fit(self, X, y, alpha=10, weights=None, signs=None):
        self.mu = X.mean(0); self.sd = X.std(0); self.sd[self.sd<1e-8]=1
        A=np.column_stack([np.ones(len(X)),(X-self.mu)/self.sd])
        w=np.ones(len(X)) if weights is None else weights
        penalty=np.eye(A.shape[1])*alpha; penalty[0,0]=0
        gram=A.T@(A*w[:,None])+penalty; rhs=A.T@(w*y)
        self.beta=np.linalg.solve(gram,rhs)
        if signs is not None:
            # Descenso por coordenadas para ridge con restricciones de signo.
            # Evita que colinealidad histórica convierta ayudas en caídas causales.
            for _ in range(1500):
                old=self.beta.copy()
                for k in range(len(self.beta)):
                    b=(rhs[k]-gram[k]@self.beta+gram[k,k]*self.beta[k])/gram[k,k]
                    sign=signs.get(k-1,0)
                    self.beta[k]=max(b,0) if sign==1 else min(b,0) if sign==-1 else b
                if np.max(np.abs(old-self.beta))<1e-9: break
        return self
    def predict(self,X):
        return self.beta[0]+((X-self.mu)/self.sd)@self.beta[1:]

def features(df, channel):
    cols=['t']+ECON[channel]+['dias_laborables','semana_santa']+EVENTS
    a=df[cols].to_numpy(float)
    return np.column_stack([a]+[(df.mes.to_numpy()==m).astype(float) for m in range(2,13)])

def macro_future(macro, cutoff, calendar, scenario, cfg):
    last=macro[macro.t<=cutoff].iloc[-1]
    fut=pd.DataFrame([last.to_dict() for _ in range(len(calendar))])
    for c in ['t','mes','dias_laborables','semana_santa']: fut[c]=calendar[c].to_numpy()
    fut[EVENTS]=0
    sc=cfg['escenarios'][scenario]
    fut['paro'] += sc['paro_pp']
    fut['confianza_consumidor'] += sc['confianza_puntos']
    fut['tipo_credito_consumo'] += sc['credito_pp']
    fut['pib_var'] += sc['pib_pp']
    # Preservar el patrón estacional de la actividad y turismo, con nivel reciente.
    prev=macro[(macro.t>cutoff-12)&(macro.t<=cutoff)].set_index('mes')
    fut['indice_actividad']=[prev.loc[m,'indice_actividad']*(1+sc['actividad_pct']) for m in fut.mes]
    fut['viajeros_var']=[prev.loc[m,'viajeros_var']+sc['turismo_pp'] for m in fut.mes]
    fut.loc[fut.t<=cutoff+sc['meses_caida'],'caida_tras_adelanto']=1
    if sc['ayuda_desde_mes']:
        fut.loc[(fut.t-cutoff)>=sc['ayuda_desde_mes'],'incentivo_publico']=1
    return fut

def fit_market(market, macro, cutoff, alpha=10):
    models={}
    for seg in SEG:
        for ch in CHANNELS:
            y=market[(market.segmento==seg)&(market.canal==ch)&(market.t<=cutoff)].sort_values('t')
            x=macro.set_index('t').loc[y.t].reset_index()
            # Se conservan todos los años, con más peso para los recientes.
            weights=np.exp((x.t.to_numpy()-cutoff)/60)
            names=['t']+ECON[ch]+['dias_laborables','semana_santa']+EVENTS
            positive=['confianza_consumidor','pib_var','indice_actividad','viajeros_var','dias_laborables','incentivo_publico','adelanto_compras','subida_iva']
            negative=['paro','tipo_credito_consumo','semana_santa','caida_tras_adelanto']
            signs={i:1 if nm in positive else -1 for i,nm in enumerate(names) if nm in positive+negative}
            model=Ridge().fit(features(x,ch),np.log1p(y.unidades.to_numpy()),alpha,weights,signs)
            fitted=np.expm1(model.predict(features(x,ch)))
            # Anclaje del nivel reciente, no al pico aislado de diciembre.
            anchor=(y.unidades.to_numpy()[-12:].sum()+1)/(fitted[-12:].sum()+1)
            models[seg,ch]=(model,anchor)
    return models

def market_predict(models, future):
    return {(s,c):np.maximum(0,np.expm1(m.predict(features(future,c)))*a)
            for (s,c),(m,a) in models.items()}

def clean_history(ventas,stock,market,macro,models,cutoff):
    v=ventas[ventas.t<=cutoff].copy()
    v['clientes']=v.unidades-v.u_automatriculacion
    v['imputacion_falta']=0.; v['factor_sucesos']=1.
    for seg in SEG:
        for ch in CHANNELS:
            ids=v[(v.segmento==seg)&(v.canal==ch)].sort_values('t').index
            g=v.loc[ids]; mk=market[(market.segmento==seg)&(market.canal==ch)].set_index('t')
            h=stock[stock.segmento==seg].set_index('t')
            clients=g.clientes.to_numpy(float); imputed=np.zeros(len(g))
            for j,t in enumerate(g.t):
                if t not in h.index or j<12: continue
                past=v[(v.segmento==seg)&(v.t<t)&(v.t>=t-12)]
                avg=(past.unidades-past.u_automatriculacion).sum()/12
                # Stock muy bajo solo es indicio, no prueba de ventas perdidas.
                if h.loc[t,'stock_total']<0.20*avg:
                    ts=g.t.iloc[max(0,j-12):j]
                    share=clients[max(0,j-12):j].sum()/max(mk.loc[ts,'unidades'].sum(),1)
                    latent=mk.loc[t,'unidades']*share
                    imputed[j]=min(max(latent-clients[j],0),0.20*max(clients[j],1))
            v.loc[ids,'imputacion_falta']=imputed
            x=macro.set_index('t').loc[g.t].reset_index(); zero=x.copy(); zero[EVENTS]=0
            mod=models[seg,ch][0]
            factors=np.exp(mod.predict(features(x,ch))-mod.predict(features(zero,ch)))
            v.loc[ids,'factor_sucesos']=factors
    v['demanda_ajustada']=(v.clientes+v.imputacion_falta)/v.factor_sucesos
    v['adelanto_estimado']=(v.clientes+v.imputacion_falta)-v.demanda_ajustada
    return v

def shares(clean, market, cutoff):
    ans={}; audit=[]
    for seg in SEG:
        for ch in CHANNELS:
            v=clean[(clean.segmento==seg)&(clean.canal==ch)].sort_values('t')
            # La cuota neta usa mercado observado: el efecto común de sucesos se cancela.
            active=v[v.unidades>0]
            if active.empty:
                ans[seg,ch]=(0.,0.); continue
            start=max(cutoff-11,int(active.t.min()))
            recent=v[v.t>=start]
            mk=market[(market.segmento==seg)&(market.canal==ch)&(market.t>=start)&(market.t<=cutoff)]
            share=(recent.clientes+recent.imputacion_falta).sum()/max(mk.unidades.sum(),1)
            prev=v[(v.t>=start-12)&(v.t<=cutoff-12)]
            pm=market[(market.segmento==seg)&(market.canal==ch)&(market.t>=start-12)&(market.t<=cutoff-12)]
            prevshare=(prev.clientes+prev.imputacion_falta).sum()/max(pm.unidades.sum(),1)
            # Tendencia amortiguada: mitad del cambio anual; límite +/-20%.
            trend=np.clip(0.5*np.log(max(share,1e-8)/max(prevshare,1e-8)),-0.20,0.20) if len(active)>=24 else 0.
            ans[seg,ch]=(share,trend)
            audit.append(dict(segmento=seg,canal=ch,cuota_neta=share,tendencia_log_anual=trend,meses_historia=len(active)))
    return ans,pd.DataFrame(audit)

def demand_predict(mp, quota, future, segmentos, cfg, scenario, cutoff, launches=True):
    out=np.zeros((len(future),7)); rows=[]
    sc=cfg['escenarios'][scenario]
    for j,s in enumerate(SEG):
        newfrac=segmentos.loc[s,'codigos_nuevos_A013']/segmentos.loc[s,'codigos_A013'] if launches else 0
        for ch in CHANNELS:
            share,trend=quota[s,ch]
            q=share*np.exp(trend*np.minimum((future.t.to_numpy()-cutoff)/12,1))
            launch=cfg['lanzamiento_mes']+(sc['retraso_lanzamiento_meses'] if s=='CSUV' else 0)
            q*=1+sc['efecto_producto']*newfrac*((future.t.to_numpy()-cutoff)>=launch)
            d=mp[s,ch]*np.minimum(q,0.95)*sc['combustible_factor']
            out[:,j]+=d
            rows.extend(dict(escenario=scenario,t=int(t),segmento=s,canal=ch,mercado=float(m),cuota=float(qq),demanda=float(dd)) for t,m,qq,dd in zip(future.t,mp[s,ch],q,d))
    return out,rows

def pipeline(stock,market,macro,models,cutoff=144):
    vals=[]
    future=macro[macro.t>cutoff-12].copy()
    future[EVENTS]=0
    neutral=market_predict(models,future)
    for s in SEG:
        h=stock[(stock.segmento==s)&(stock.t>cutoff-6)&(stock.t<=cutoff)]
        # Nivel de wholesale reciente por patrón estacional de mercado sin sucesos.
        season=sum(neutral[s,c] for c in CHANNELS)
        season=season/season.mean()
        level=np.nanmean(h.wholesale.to_numpy()/season[h.mes.to_numpy()-1])
        vals.append(np.rint(level*season[:2]))
    return np.array(vals).T.astype(int)

def simulate(demand,base,stock0,pipe,seg,ss,config,scenario='central',n=1000,seed=1,
             sigma_rel=None,rho=None,noise=True,transfer_cap=None):
    rng=np.random.default_rng(seed); H=12
    # Cohortes: siete iniciales, más una entrada por mes.
    age0=np.array([15,45,75,105,135,165,195],float)
    initial=np.column_stack([stock0.s_0_90/3]*3+[stock0.s_91_180/3]*3+[stock0.s_mas_180])
    cohorts=np.zeros((n,7,19)); cohorts[:,:,:7]=initial[None,:,:]
    ages=np.tile(np.r_[age0,np.zeros(12)],(7,1))
    arrivals=np.zeros((n,15,7)); arrivals[:,:2,:]=pipe
    # Decisión inicial (diciembre A012) para la llegada de marzo A013.
    arrivals[:,2,:]=np.ceil(np.maximum(0,base[2]+ss-(initial.sum(1)+pipe.sum(0)-base[:2].sum(0))))
    production=np.zeros((n,12,7)); bias=np.ones((n,7)); latent=np.zeros((n,7))
    sc=config['escenarios'][scenario]; metrics={k:np.zeros((n,7)) for k in
        ['demanda','ventas','fabricados','llegadas','stock_medio','viejos90','stock_final','stock_eur','perdidas_u','perdidas_eur','transfers_u','transfers_eur','vm_eur','cvp_eur','co2_eur','arancel_eur','interes_red_eur','coste_vehiculos_vendidos_eur']}
    gb=seg.beneficio_bruto_marca_eur.to_numpy(); pff=seg.pff_medio.to_numpy()
    cost=pff-seg.margen_bruto_conc_eur.to_numpy()-gb
    co2=seg.prima_co2_eur.to_numpy()*sc['co2']; tariff=cost*sc['arancel_pct']
    vm=np.column_stack([seg.vm_real_0_90_eur,seg.vm_real_91_180_eur,seg.vm_real_mas_180_eur])
    cap=config['transfer_cap_demanda'] if transfer_cap is None else transfer_cap
    paths=[]; max_balance_error=0.; opening=initial.sum(1)
    for t in range(H):
        before=cohorts.sum(2)
        cohorts[:,:,7+t]=arrivals[:,t,:]
        ages[:,7+t]=0
        if noise:
            common=rng.normal(size=(n,1)); specific=rng.normal(size=(n,7))
            eps=np.sqrt(config['correlacion_segmentos'])*common+np.sqrt(1-config['correlacion_segmentos'])*specific
            latent=rho*latent+np.sqrt(1-rho**2)*eps
            # Lognormal con media corregida; varianza del proceso inicial explícita.
            variance=1-rho**(2*(t+1))
            real=np.rint(demand[t]*np.exp(sigma_rel*latent-0.5*sigma_rel**2*variance))
        else: real=np.tile(demand[t],(n,1))
        residual=real.copy(); sold=np.zeros((n,7)); vmcost=np.zeros((n,7)); hold=np.zeros((n,7)); credit=np.zeros((n,7))
        # Orden FIFO por edad; la cohorte inicial >180 siempre sale primero.
        order=np.argsort(-ages[0,:7+t+1])
        for k in order:
            a=ages[:,k]; qty=cohorts[:,:,k].copy(); take=np.minimum(qty,residual)
            residual-=take; cohorts[:,:,k]-=take; sold+=take
            age_sale=a+15
            bucket=np.where(age_sale<=90,0,np.where(age_sale<=180,1,2))
            vmcost+=take*vm[np.arange(7),bucket]
            hold+=2*(take*np.clip(180-a,0,15)+(qty-take)*np.clip(180-a,0,30))
            # Intereses del concesionario, separados del margen de la marca.
            for dur,q in [(15,take),(30,qty-take)]:
                low=np.clip(90-a,0,dur); high=np.clip(180-a,0,dur)-low
                credit+=q*(low*seg.credito_dia_0_90_eur.to_numpy()+high*seg.credito_dia_91_180_eur.to_numpy())
        viable=(0.8*gb-vm[:,0]-co2-tariff)>0
        transfer=np.minimum(residual,np.floor(real*cap))*viable
        lost=residual-transfer; sold+=transfer; vmcost+=transfer*vm[:,0]
        tc=transfer*0.20*gb
        margin=sold*(gb-co2-tariff)-vmcost-tc-hold
        after=cohorts.sum(2); ages[:,:7+t+1]+=30
        max_balance_error=max(max_balance_error,float(np.max(np.abs(after-(before+arrivals[:,t,:]-(sold-transfer))))))
        vals={'demanda':real,'ventas':sold,'llegadas':arrivals[:,t,:], 'stock_medio':(before+arrivals[:,t,:]-(sold-transfer)/2)/12,
              'stock_eur':hold,'perdidas_u':lost,'perdidas_eur':lost*np.maximum(gb-vm[:,0]-co2-tariff,0),
              'transfers_u':transfer,'transfers_eur':tc,'vm_eur':vmcost,'cvp_eur':margin,
              'co2_eur':sold*co2,'arancel_eur':sold*tariff,'interes_red_eur':credit,
              'coste_vehiculos_vendidos_eur':sold*cost}
        for k,val in vals.items(): metrics[k]+=val
        paths.extend(dict(escenario=scenario,mes=t+1,segmento=s,demanda=real[:,j].mean(),ventas=sold[:,j].mean(),llegadas=arrivals[:,t,j].mean(),stock_final=after[:,j].mean(),cvp=margin[:,j].mean()) for j,s in enumerate(SEG))
        # Se observa demanda servida + solicitudes no servidas, no el escenario futuro.
        bias=np.clip((1-config['ganancia_revision'])*bias+config['ganancia_revision']*(real/np.maximum(base[t],1)),0.4,1.8)
        future=base[t+1:t+4][None,:,:]*bias[:,None,:]
        projected=after+arrivals[:,t+1:t+3,:].sum(1)-future[:,:2,:].sum(1)
        orderqty=np.ceil(np.maximum(0,future[:,2,:]+ss-projected))
        # La parada afecta producción de mayo CSUV; no se recupera automáticamente.
        if t+1==sc['parada_mes']: orderqty[:,SEG.index(sc['parada_segmento'])]=0
        production[:,t,:]=orderqty; arrivals[:,t+3,:]=orderqty
    metrics['fabricados']=production.sum(1)
    metrics['stock_final']=cohorts.sum(2)
    metrics['viejos90']=(cohorts*(ages[None,:,:]>90)).sum(2)
    metrics['cobertura']=metrics['stock_medio']/np.maximum(metrics['ventas']/12,1)
    metrics['pipeline_final']=arrivals[:,12:15,:].sum(1)
    assert max_balance_error<1e-6
    assert np.min(cohorts)>=-1e-6
    return metrics,production,arrivals,pd.DataFrame(paths)

def main(n=1000,seed=20261008):
    cfg=json.loads((ROOT/'config.json').read_text()); out=ROOT/'resultados'; out.mkdir(exist_ok=True)
    sales,stock,market,macro,seg,calendar,codes=[read(f) for f in ['ventas_mensual.csv','stock_mensual.csv','mercado_mensual.csv','macro_mensual.csv','segmentos.csv','calendario_A013.csv','codigos.csv']]
    seg=seg.set_index('segmento').loc[SEG]
    assert sales.unidades.sum()==125030 and market[market.t>=25].marca_propia.sum()==125030
    assert not codes.codigo_modelo.isna().any() and 'NA' in codes.codigo_modelo.values
    assert not sales.duplicated(['t','segmento','canal']).any()
    stock=stock.sort_values(['segmento','t']); stock['residuo_balance']=stock.groupby('segmento').stock_total.diff()-stock.wholesale+sales.groupby(['segmento','t']).unidades.sum().reindex(pd.MultiIndex.from_frame(stock[['segmento','t']])).to_numpy()
    stock.to_csv(out/'auditoria_stock.csv',index=False)
    # Elegir penalización únicamente con A010/A011; A012 queda fuera.
    tuning=[]
    for a in [1,10,30]:
        for cut in [108,120]:
            mods=fit_market(market,macro,cut,a); fut=macro[(macro.t>cut)&(macro.t<=cut+12)]
            pred=market_predict(mods,fut); error=den=0
            for (s,c),p in pred.items():
                truth=market[(market.segmento==s)&(market.canal==c)&(market.t>cut)&(market.t<=cut+12)].sort_values('t').unidades.to_numpy()
                error+=np.abs(p-truth).sum(); den+=truth.sum()
            tuning.append(dict(alpha=a,corte=cut,wape=error/den))
    tuning=pd.DataFrame(tuning); tuning.to_csv(out/'seleccion_modelo.csv',index=False)
    alpha=float(tuning.groupby('alpha').wape.mean().idxmin())
    models11=fit_market(market,macro,132,alpha)
    clean11=clean_history(sales,stock,market,macro,models11,132); quota11,_=shares(clean11,market,132)
    valid=[]; errors=[]
    for mode in ['condicional','ex_ante']:
        fut=macro[macro.t>132].copy()
        if mode=='ex_ante':
            # Calendario conocido; macro congelada y sin sucesos futuros anticipados.
            fut=macro_future(macro,132,fut,'central',cfg); fut[EVENTS]=0
        mp=market_predict(models11,fut)
        forecast,_=demand_predict(mp,quota11,fut,seg,cfg,'central',132,launches=False)
        for j,s in enumerate(SEG):
            g=sales[(sales.segmento==s)&(sales.t>132)].groupby('t')[['unidades','u_automatriculacion']].sum()
            truth=(g.unidades-g.u_automatriculacion).to_numpy()
            naive=sales[(sales.segmento==s)&(sales.t>120)&(sales.t<=132)].groupby('t')[['unidades','u_automatriculacion']].sum()
            naive=(naive.unidades-naive.u_automatriculacion).to_numpy()
            valid.append(dict(modo=mode,segmento=s,real=truth.sum(),prevision=forecast[:,j].sum(),wape=np.abs(forecast[:,j]-truth).sum()/max(truth.sum(),1),sesgo=(forecast[:,j]-truth).sum()/max(truth.sum(),1),wape_naive=np.abs(naive-truth).sum()/max(truth.sum(),1)))
            errors.extend(dict(modo=mode,mes=t+1,segmento=s,real=truth[t],prevision=forecast[t,j],error=truth[t]-forecast[t,j]) for t in range(12))
    valid=pd.DataFrame(valid); valid.to_csv(out/'validacion_A012.csv',index=False)
    errors=pd.DataFrame(errors); errors.to_csv(out/'errores_A012.csv',index=False)
    models=fit_market(market,macro,144,alpha); clean=clean_history(sales,stock,market,macro,models,144)
    clean.to_csv(out/'demanda_historica_limpia.csv',index=False)
    quota,qa=shares(clean,market,144); qa.to_csv(out/'cuotas.csv',index=False)
    clean.groupby('anio')[['unidades','u_automatriculacion','clientes','imputacion_falta','adelanto_estimado','demanda_ajustada']].sum().to_csv(out/'crecimiento_limpio.csv')
    coeff=[]
    for (s,ch),(mod,a) in models.items():
        names=['t']+ECON[ch]+['dias_laborables','semana_santa']+EVENTS+[f'mes_{m}' for m in range(2,13)]
        coeff.extend(dict(segmento=s,canal=ch,variable=nm,coef_log=coef/sd) for nm,coef,sd in zip(names,mod.beta[1:],mod.sd))
    pd.DataFrame(coeff).to_csv(out/'coeficientes_mercado.csv',index=False)
    ext=calendar.iloc[:3].copy(); ext.t+=12
    cal15=pd.concat([calendar,ext],ignore_index=True)
    forecasts={}; frows=[]; macros=[]
    for scenario in cfg['escenarios']:
        fut=macro_future(macro,144,cal15,scenario,cfg); fut['escenario']=scenario; macros.append(fut)
        forecasts[scenario],rows=demand_predict(market_predict(models,fut),quota,fut,seg,cfg,scenario,144)
        frows+=rows
    pd.concat(macros).to_csv(out/'supuestos_macro_A013.csv',index=False)
    df_forecast=pd.DataFrame(frows)
    df_forecast.to_csv(out/'prevision_canal.csv',index=False)
    df_forecast[df_forecast.t<=156].groupby(['escenario','t','segmento']).demanda.sum().reset_index().to_csv(out/'demanda_A013_mensual.csv',index=False)
    base=forecasts['central']; hist=stock[stock.t==144].set_index('segmento').loc[SEG]
    pipe=pipeline(stock,market,macro,models)
    pd.DataFrame(pipe,columns=SEG,index=['Ene','Feb']).to_csv(out/'transito_inicial.csv')
    rel=[]; rho=[]
    for j,s in enumerate(SEG):
        e=errors[(errors.modo=='ex_ante')&(errors.segmento==s)]
        if s=='CSUV': rel.append(cfg['sigma_rel_cold_start']);rho.append(.30);continue
        r=(e.real-e.prevision).to_numpy()/np.maximum(e.prevision.to_numpy(),1)
        rel.append(float(np.clip(np.sqrt(np.mean(r*r)),.10,.60)))
        rr=np.corrcoef(r[:-1],r[1:])[0,1];rho.append(float(np.clip(rr if np.isfinite(rr) else 0,0,.65)))
    rel=np.array(rel);rho=np.array(rho)
    z=np.array([cfg['z'][s] for s in SEG]); sigma=rel*base[:12].mean(0)
    # Varianza de la suma de tres errores AR(1): 3+4*rho+2*rho^2.
    ss=np.ceil(z*sigma*np.sqrt(3+4*rho+2*rho**2))
    pd.DataFrame(dict(segmento=SEG,sigma_rel=rel,rho=rho,z=z,stock_seguridad=ss)).to_csv(out/'stock_seguridad.csv',index=False)
    seg.loc['CSUV','vm_real_mas_180_eur']=seg.loc['CSUV','vm_real_91_180_eur']+np.nanmedian(seg.vm_real_mas_180_eur-seg.vm_real_91_180_eur)
    metrics,plan,arr,paths=simulate(base,base,hist,pipe,seg,ss,cfg,noise=False,n=1)
    plan=plan[0].astype(int)
    pd.DataFrame(plan,index=range(1,13),columns=SEG).rename_axis('mes_fabricacion').to_csv(out/'plan_fabricacion_A013.csv')
    pd.DataFrame(arr[0,:12].astype(int),index=range(1,13),columns=SEG).rename_axis('mes_llegada').to_csv(out/'plan_llegadas_A013.csv')
    rows=[]; allpaths=[]; samples=[]; uncertainty=[]
    for scenario in cfg['escenarios']:
        met,production,arrivals,path=simulate(forecasts[scenario],base,hist,pipe,seg,ss,cfg,scenario,n,seed,rel,rho)
        allpaths.append(path)
        for j,s in enumerate(SEG+['TOTAL']):
            vals={k:(v[:,j] if s!='TOTAL' else v.sum(1)) for k,v in met.items() if k!='cobertura'}
            vals['cobertura']=vals['stock_medio']/np.maximum(vals['ventas']/12,1)
            rows.append(dict(escenario=scenario,segmento=s,**{k:float(v.mean()) for k,v in vals.items()}))
            uncertainty.append(dict(escenario=scenario,segmento=s,**{f'{k}_p{p}':float(np.percentile(vals[k],p)) for k in ['demanda','ventas','cvp_eur'] for p in [5,50,95]}))
            if s=='TOTAL': samples.extend(dict(escenario=scenario,replica=i,**{k:float(v[i]) for k,v in vals.items()}) for i in range(n))
    results=pd.DataFrame(rows); results.to_csv(out/'tabla5.csv',index=False)
    pd.DataFrame(uncertainty).to_csv(out/'intervalos.csv',index=False)
    pd.concat(allpaths).to_csv(out/'simulacion_mensual.csv',index=False)
    pd.DataFrame(samples).to_csv(out/'replicas_totales.csv',index=False)
    # Sensibilidades independientes, misma semilla y plan/política iniciales.
    sensitivities=[]
    for label,pp,zz,cap in [('transito_-25',pipe*.75,ss,None),('transito_+25',pipe*1.25,ss,None),('sin_transfers',pipe,ss,0),('ss_-25',pipe,ss*.75,None),('ss_+25',pipe,ss*1.25,None)]:
        met,*_=simulate(base,base,hist,pp,seg,zz,cfg,'central',n,seed,rel,rho,transfer_cap=cap)
        sensitivities.append(dict(prueba=label,**{k:float(v.sum(1).mean()) for k,v in met.items() if k in ['cvp_eur','stock_medio','perdidas_u','transfers_u','stock_eur']}))
    pd.DataFrame(sensitivities).to_csv(out/'sensibilidades.csv',index=False)
    manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'data').glob('*.csv'))}
    (out/'ejecucion.json').write_text(json.dumps(dict(n=n,seed=seed,alpha=alpha,sha256_datos=manifest,version_numpy=np.__version__,version_pandas=pd.__version__,stock_inicial=int(hist.stock_total.sum()),max_residuo_stock=float(stock.residuo_balance.abs().max())),indent=2))
    print(results[results.segmento=='TOTAL'].to_string(index=False))
    print('\nPlan fábrica:',plan.sum(), '\nValidación:\n',valid.to_string(index=False))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--n',type=int,default=1000); p.add_argument('--seed',type=int,default=20261008)
    args=p.parse_args(); main(args.n,args.seed)
