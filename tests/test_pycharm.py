""" Tests of kinetic_datanator

:Author: Yosef Roth <yosefdroth@gmail.com>
:Date: 2017-04-06
:Copyright: 2017, Karr Lab
:License: MIT
"""

from os import path
from kinetic_datanator import datanator
import openpyxl
import os
import sys
import unittest


class TestProgram(unittest.TestCase):
	
	def test_datanator(self):
		# Test getting kinetic data about a reaction that is releveant for Mycoplasma pneumoniae

		species = 'mycoplasma pneumoniae'
		
		input_file_name = path.join(path.dirname(__file__), "fixtures", "ump_kinase.xlsx")
		
		out_dir = path.join(path.dirname(__file__), "output")
		if not path.isdir(out_dir):
			os.makedirs(out_dir)
		output_file_name = path.join(out_dir, "ump_kinase.xlsx")
		
		# get kinetic data for reations in Excel sheet
		rxns = datanator.get_kinetic_data(input_file_name, output_file_name, species)

		# test correct number of output reactions
		self.assertEqual(len(rxns), 1)

		# test outputted reaction is UMP kinases
		rxn = rxns[0]
		self.assertEqual(rxn.id, 'ump_kinase')

		#test the formatted data fields
		self.assertEqual(rxn.reaction_ids, ['201'])

		#median_km_entry is an object of the Entry class found in the sabio_interface module
		#the following are a series of tests that make sure that the entry fields are
		#filled in properly
		median_entry = rxn.km_data.median_entry
		self.assertNotEqual(median_entry, None)
		self.assertEqual(median_entry.entry_id, '17927')
		self.assertEqual(median_entry.vmax, '0.00665')
		self.assertEqual(median_entry.proximity, 6)