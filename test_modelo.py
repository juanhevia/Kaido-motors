"""Pruebas de invariantes de negocio. Ejecutar: python -m unittest -v."""
import json, unittest
import numpy as np
import pandas as pd
from modelo import ROOT, SEG, read, simulate

class SimulacionTests(unittest.TestCase):
    def setUp(self):
        self.cfg=json.loads((ROOT/'config.json').read_text())
        self.seg=read('segmentos.csv').set_index('segmento').loc[SEG].fillna(2600)
        self.stock=read('stock_mensual.csv').query('t==144').set_index('segmento').loc[SEG].copy()
        self.stock[['s_0_90','s_91_180','s_mas_180']]=0
        self.base=np.full((15,7),100.)
        self.pipe=np.full((2,7),100.)
        self.ss=np.zeros(7)
    def sim(self,d=None,**kw):
        return simulate(self.base if d is None else d,self.base,self.stock,self.pipe,self.seg,self.ss,self.cfg,n=1,noise=False,**kw)
    def test_equilibrio_sin_faltas(self):
        m,p,a,_=self.sim()
        np.testing.assert_allclose(m['ventas'],1200)
        np.testing.assert_allclose(m['perdidas_u'],0)
        np.testing.assert_allclose(m['stock_final'],0)
        np.testing.assert_allclose(m['stock_medio'],50)
        np.testing.assert_allclose(m['stock_eur'],36000) # 100*15*2*12
        np.testing.assert_allclose(m['fabricados'],p.sum(1))
    def test_shock_respeta_tres_meses(self):
        _,_,a,_=self.sim()
        d=self.base.copy();d[0]*=2
        m,p,b,_=self.sim(d)
        np.testing.assert_allclose(a[:,:3],b[:,:3])
        self.assertTrue(np.any(b[:,3]>a[:,3]))
        np.testing.assert_allclose(m['demanda'],m['ventas']+m['perdidas_u'])
    def test_tope_180_dias_y_fifo(self):
        self.base[:]=0;self.pipe[:]=0
        self.stock['s_mas_180']=100
        m,*_=self.sim()
        np.testing.assert_allclose(m['stock_eur'],0)
        np.testing.assert_allclose(m['interes_red_eur'],0)
        np.testing.assert_allclose(m['viejos90'],100)
    def test_transfer_y_margen_sin_doble_coste(self):
        self.pipe[:]=0
        m,*_=self.sim()
        gb=self.seg.beneficio_bruto_marca_eur.to_numpy()
        np.testing.assert_allclose(m['cvp_eur'],m['ventas']*gb-m['vm_eur']-m['stock_eur']-m['transfers_eur'])
        np.testing.assert_allclose(m['transfers_eur'],m['transfers_u']*.2*gb)
        self.assertTrue(np.all(m['transfers_u']<=m['demanda']*.1))
    def test_datos_y_tabla5(self):
        v=read('ventas_mensual.csv');mk=read('mercado_mensual.csv')
        a=v.groupby(['t','segmento','canal']).unidades.sum()
        b=mk[mk.t>=25].set_index(['t','segmento','canal']).marca_propia.reindex(a.index)
        np.testing.assert_array_equal(a,b)
        table=pd.read_csv(ROOT/'resultados/tabla5.csv')
        for _,g in table.groupby('escenario'):
            for col in ['ventas','fabricados','stock_medio','viejos90','stock_eur','vm_eur','cvp_eur','perdidas_u','transfers_u']:
                self.assertAlmostEqual(g[g.segmento!='TOTAL'][col].sum(),float(g[g.segmento=='TOTAL'][col].iloc[0]),places=5)

if __name__=='__main__': unittest.main()
