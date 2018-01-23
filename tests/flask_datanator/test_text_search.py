from kinetic_datanator.flask_datanator import text_search
import unittest


class TestTextSearchSession(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.sesh = text_search.TextSearchSession()

    def test_collect_data_objects(self):
        search_dict = self.sesh.collect_data_objects('2-Oxopentanoate')
        self.assertEqual(set([c.compound_name for c in search_dict['Compound']]),
                         set([u'4-Hydroxy-2-oxopentanoate', u'(S)-4-Amino-5-oxopentanoate',
                              u'(R)-3-Hydroxy-3-methyl-2-oxopentanoate', u'(R) 2,3-Dihydroxy-3-methylvalerate',
                              u'2-Oxopentanoate', u'Ketoleucine', u'4-Methyl-2-oxopentanoate',
                              u'2-Isopropyl-3-oxosuccinate']))

        search_dict = self.sesh.collect_data_objects('MCM complex')
        self.assertEqual(set([c.su_cmt for c in search_dict['ProteinComplex']]),
                         set([u'None', u'Q91876(1)|P55862(1)|Q7ZY18(1)|P55861(1)|P30664(1)|P49739(1)',
                         u'P29469(1)|P53091(1)|P30665(1)|P24279(1)|P38132(1)|P29496(1)',
                         u'O75001(1)|P40377(1)|P41389(1)|P49731(1)|P29458(1)|P30666(1)',
                         u'Q9VGW6(1)|P49735(1)|Q26454(1)|Q9V461(1)|Q9XYU0(1)|Q9XYU1(1)',
                         u'P25206(1)|Q61881(1)|P49717(1)|P97310(1)|P97311(1)|P49718(1)',
                         u'P33991(1)|P33993(1)|P33992(1)|P25205(1)|Q14566(1)|P49736(1)']))

        search_dict = self.sesh.collect_data_objects('P49418')
        self.assertEqual(set([c.interaction for c in search_dict['ProteinInteractions']]),
                        set([u'intact:EBI-7121760|mint:MINT-8094677', u'intact:EBI-7121870|mint:MINT-8094737',
                        u'intact:EBI-7121552|mint:MINT-16056', u'intact:EBI-7122020|mint:MINT-8094831',
                        u'intact:EBI-7121659|mint:MINT-8094627', u'intact:EBI-7121975|mint:MINT-8094817',
                        u'intact:EBI-7122056|mint:MINT-8094848', u'intact:EBI-7121816|mint:MINT-8094722',
                        u'intact:EBI-7121780|mint:MINT-8094706', u'intact:EBI-7121634|mint:MINT-8094596',
                        u'intact:EBI-7121926|mint:MINT-8094793', u'intact:EBI-7121710|mint:MINT-8094651',
                        u'intact:EBI-7121911|mint:MINT-8094755']))



    def test_return_information(self):
        ans = self.sesh.return_information('L-Histidine')
        for items in ans[1]['MetaboliteConcentration']:
            if items:
                obs = [c for c in items if c.observable.specie.name == 'L-Histidine']
                if obs:
                    break
                self.assertEqual(set([c.value for c in obs]), set(
                    [97.5, 0.22, 52.4, 175.0, 235.33, 67.6]))

        ans = self.sesh.return_information('Q725Q1')
        # for items in

    def test_protein_abundance_query(self):
        pass
