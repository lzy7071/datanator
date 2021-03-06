# -*- coding: utf-8 -*-

""" Tests of sabio_rk

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Author: Saahith Pochiraju <saahith116@gmail.com>
:Date: 2017-04-26
:Copyright: 2017, Karr Lab
:License: MIT
"""

from datanator.core import data_model
from datanator.data_source import sabio_rk
from datanator.api.query import reaction_kinetics
from datanator.util import taxonomy_util, molecule_util
from datanator.core import models, common_schema
import unittest
import random
import tempfile
import shutil

@unittest.skip('skip')
class TestReactionKineticsQuery(unittest.TestCase):
    """
    Tests for 10000 entry limited Common Schema on Karr Lab Server

    Used for development purposes
    """

    @classmethod
    def setUpClass(cls):
        cls.cache_dirname = tempfile.mkdtemp()
        cls.flk = common_schema.CommonSchema(cache_dirname=cls.cache_dirname)

        cls.q = reaction_kinetics.ReactionKineticsQuery(cache_dirname=cls.cache_dirname, include_variants=True)

        cls.reaction = data_model.Reaction(
            participants = [
                data_model.ReactionParticipant(
                    specie = data_model.Specie(
                        id = 'Dihydrofolate',
                        structure = 'InChI=1S/C19H21N7O6/c20-19-25-15-14(17(30)26-19)23-11(8-22-15)'+\
                        '7-21-10-3-1-9(2-4-10)16(29)24-12(18(31)32)5-6-13(27)28/h1-4,12,21H,5-8H2,'+\
                        '(H,24,29)(H,27,28)(H,31,32)(H4,20,22,25,26,30)'),
                    coefficient = -1),
                data_model.ReactionParticipant(
                    specie = data_model.Specie(
                        id = 'NADPH',
                        structure = 'InChI=1S/C21H30N7O17P3/c22-17-12-19(25-7-24-17)28(8-26-12)21-16'+\
                        '(44-46(33,34)35)14(30)11(43-21)6-41-48(38,39)45-47(36,37)40-5-10-13(29)15(31)'+\
                        '20(42-10)27-3-1-2-9(4-27)18(23)32/h1,3-4,7-8,10-11,13-16,20-21,29-31H,2,5-6H2,'+\
                        '(H2,23,32)(H,36,37)(H,38,39)(H2,22,24,25)(H2,33,34,35)'),
                    coefficient = -1),
                data_model.ReactionParticipant(
                    specie = data_model.Specie(
                        id = 'H+',
                        structure = 'InChI=1S/H'),
                    coefficient = -1),
                data_model.ReactionParticipant(
                    specie = data_model.Specie(
                        id = 'NADP+',
                        structure = 'InChI=1S/C21H28N7O17P3/c22-17-12-19(25-7-24-17)28(8-26-12)21-16('+\
                        '44-46(33,34)35)14(30)11(43-21)6-41-48(38,39)45-47(36,37)40-5-10-13(29)15(31)20'+\
                        '(42-10)27-3-1-2-9(4-27)18(23)32/h1-4,7-8,10-11,13-16,20-21,29-31H,5-6H2,(H7-,22'+\
                        ',23,24,25,32,33,34,35,36,37,38,39)/p+1'),
                    coefficient = 1),
                data_model.ReactionParticipant(
                    specie = data_model.Specie(
                        id = '5,6,7,8-Tetrahydrofolate',
                        structure = 'InChI=1S/C19H23N7O6/c20-19-25-15-14(17(30)26-19)23-11(8-22-15)7-21-'+\
                        '10-3-1-9(2-4-10)16(29)24-12(18(31)32)5-6-13(27)28/h1-4,11-12,21,23H,5-8H2,(H,24,29'+\
                        ')(H,27,28)(H,31,32)(H4,20,22,25,26,30)'),
                    coefficient = 1)
        ])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.cache_dirname)

    def test_get_observed_result(self):

        vals = self.q.run(self.reaction).observed_results

        for val in vals:
            sabiork_id = next(xr.id for xr in val.observable.interaction.cross_references if xr.namespace == 'sabiork.reaction')
            common_schema_kinetic_id = next(xr.id for xr in val.observable.interaction.cross_references if xr.namespace == 'common_schema.kinetic_law_id')
            if sabiork_id == '100' and common_schema_kinetic_id == '2205':
                if val.observable.property == 'Km_A':
                    self.assertEqual(val.observable.specie.name,'NADPH')
                    self.assertEqual(val.value, 7.3e-06)
                    self.assertEqual(val.error, 2.0e-07)
                    self.assertEqual(val.units, 'M')
                    break

    def test_get_reaction_by_kinetic_law_id(self):

        ans = self.q.get_reaction_by_kinetic_law_id(41438)

        self.assertEqual(ans.name, 'Squalene --> Diploptene')
        self.assertEqual(ans.kinetic_law_id, 41438)
        self.assertEqual(set([parts.specie.name for parts in ans.participants]), set(['Squalene', 'Diploptene']))
        self.assertEqual(set([parts.coefficient for parts in ans.participants]), set([-1, 1]))

    def test_get_reaction_by_metabolite(self):
        metabolite = self.flk.session.query(models.Metabolite).filter_by(metabolite_name = '2-Hydroxyisocaproate').first()

        rxn_list = self.q.get_reaction_by_metabolite(metabolite)


        self.assertEqual(rxn_list[0].get_ec_number(), '1.1.99.31')
        self.assertEqual(len(rxn_list[0].participants), 4)
        self.assertEqual(rxn_list[0].participants[0].specie.name, '2-Hydroxyisocaproate')

    def test_get_kinetic_laws_by_ec_numbers(self):

        # single EC, match_levels=4
        laws_62 = self.q.get_kinetic_laws_by_ec_numbers(['3.4.21.62'], match_levels=4).all()
        compare = self.flk.session.query(models.KineticLaw).filter_by(enzyme_id = laws_62[0].enzyme_id).all()
        ids_62 = set([c.kinetic_law_id for c in compare])
        self.assertEqual(set(l.id for l in laws_62), ids_62)

        laws_73 = self.q.get_kinetic_laws_by_ec_numbers(['3.4.21.73'], match_levels=4).all()

        compare = self.flk.session.query(models.KineticLaw).filter_by(enzyme_id = laws_73[0].enzyme_id).all()
        ids_73 = set([c.kinetic_law_id for c in compare])
        self.assertEqual(set(l.id for l in laws_73), ids_73)

        #multiple EC, match_levels=4

        laws = self.q.get_kinetic_laws_by_ec_numbers(['3.4.21.62', '3.4.21.73'], match_levels=4).all()
        self.assertEqual(set([l.id for l in laws]), ids_62 | ids_73)

        # single EC, match_levels=3
        laws_xx = self.q.get_kinetic_laws_by_ec_numbers(['3.4.21.73'], match_levels=3).all()
        self.assertEqual(len(laws_xx), 55)


    def test_get_kinetic_laws_by_structure(self):

        #Modifier
        metabolite = 'InChI=1S/Zn'
        law = self.q.get_kinetic_laws_by_structure(metabolite, role = 'modifier')
        self.assertEqual(len([c.kinetic_law_id for c in law.all() if c.kinetic_law_id <400000 ]), 24)


    def test_get_kinetic_laws_by_metabolite(self):

        #Reactant
        metabolite = self.flk.session.query(models.Metabolite).filter_by(metabolite_name = '2-Hydroxyisocaproate').first()
        law = self.q.get_kinetic_laws_by_metabolite(metabolite, role = 'reactant')
        self.assertEqual(len([c.kinetic_law_id for c in law.all() if c.kinetic_law_id <400000]), 2)

        #Product
        metabolite = self.flk.session.query(models.Metabolite).filter_by(metabolite_name = '4-Hydroxyphenylethyl alcohol').first()
        law = self.q.get_kinetic_laws_by_metabolite(metabolite, role = 'product')
        self.assertEqual(len([c.kinetic_law_id for c in law.all() if c.kinetic_law_id <400000 ]), 1)

        #Modifier
        metabolite = self.flk.session.query(models.Metabolite).filter_by(metabolite_name = 'Zn2+').first()
        law = self.q.get_kinetic_laws_by_metabolite(metabolite, role = 'modifier')
        self.assertEqual(len([c.kinetic_law_id for c in law.all() if c.kinetic_law_id <400000 ]), 24)


    def test_get_kinetic_laws_by_reaction(self):
        laws = self.q.get_kinetic_laws_by_reaction(self.reaction)

        self.assertEqual(len([l.kinetic_law_id for l in laws]), 58)


    def test_get_metabolites_by_structure(self):
        struct = self.flk.session.query(models.Structure).all()

        ans = self.q.get_metabolites_by_structure(struct[3414]._value_inchi).all()
        self.assertEqual(ans, struct[3414].metabolite)


        ans = self.q.get_metabolites_by_structure(struct[3414]._value_inchi, only_formula_and_connectivity=True).all()
        self.assertEqual(ans, struct[3414].metabolite)
