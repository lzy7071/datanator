"""empty message

Revision ID: ea8e6d48cd86
Revises: 
Create Date: 2018-02-13 12:28:26.792908

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ea8e6d48cd86'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('characteristic',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('category', sa.String(length=255), nullable=True),
    sa.Column('value', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('variable',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('category', sa.String(length=255), nullable=True),
    sa.Column('value', sa.String(length=255), nullable=True),
    sa.Column('units', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('_metadata_characteristic',
    sa.Column('_metadata_id', sa.Integer(), nullable=True),
    sa.Column('characteristic_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['_metadata_id'], ['_metadata.id'], ),
    sa.ForeignKeyConstraint(['characteristic_id'], ['characteristic.id'], )
    )
    op.create_index(op.f('ix__metadata_characteristic__metadata_id'), '_metadata_characteristic', ['_metadata_id'], unique=False)
    op.create_index(op.f('ix__metadata_characteristic_characteristic_id'), '_metadata_characteristic', ['characteristic_id'], unique=False)
    op.create_table('_metadata_variable',
    sa.Column('_metadata_id', sa.Integer(), nullable=True),
    sa.Column('variable_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['_metadata_id'], ['_metadata.id'], ),
    sa.ForeignKeyConstraint(['variable_id'], ['variable.id'], )
    )
    op.create_index(op.f('ix__metadata_variable__metadata_id'), '_metadata_variable', ['_metadata_id'], unique=False)
    op.create_index(op.f('ix__metadata_variable_variable_id'), '_metadata_variable', ['variable_id'], unique=False)
    op.create_table('rna_seq_dataset',
    sa.Column('sample_id', sa.Integer(), nullable=False),
    sa.Column('experiment_accession_number', sa.String(), nullable=True),
    sa.Column('sample_name', sa.String(), nullable=True),
    sa.Column('assay', sa.String(), nullable=True),
    sa.Column('ensembl_organism_strain', sa.String(), nullable=True),
    sa.Column('read_type', sa.String(), nullable=True),
    sa.Column('full_strain_specificity', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['sample_id'], ['physical_property.observation_id'], ),
    sa.PrimaryKeyConstraint('sample_id')
    )
    op.create_table('rna_seq_experiment',
    sa.Column('experiment_id', sa.Integer(), nullable=False),
    sa.Column('accesion_number', sa.String(), nullable=True),
    sa.Column('exp_name', sa.String(), nullable=True),
    sa.Column('has_fastq_files', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['experiment_id'], ['physical_property.observation_id'], ),
    sa.PrimaryKeyConstraint('experiment_id')
    )
    op.create_table('rnaseqdataset_rnaseqexperiment',
    sa.Column('experiment_id', sa.Integer(), nullable=True),
    sa.Column('sample_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['experiment_id'], ['rna_seq_experiment.experiment_id'], ),
    sa.ForeignKeyConstraint(['sample_id'], ['rna_seq_dataset.sample_id'], )
    )
    op.create_index(op.f('ix_rnaseqdataset_rnaseqexperiment_experiment_id'), 'rnaseqdataset_rnaseqexperiment', ['experiment_id'], unique=False)
    op.create_index(op.f('ix_rnaseqdataset_rnaseqexperiment_sample_id'), 'rnaseqdataset_rnaseqexperiment', ['sample_id'], unique=False)
    op.add_column(u'_metadata', sa.Column('description', sa.Text(), nullable=True))
    op.add_column(u'method', sa.Column('hardware', sa.String(length=255), nullable=True))
    op.add_column(u'method', sa.Column('performer', sa.String(length=255), nullable=True))
    op.add_column(u'method', sa.Column('software', sa.String(length=255), nullable=True))
    op.add_column(u'resource', sa.Column('release_date', sa.String(length=255), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column(u'resource', 'release_date')
    op.drop_column(u'method', 'software')
    op.drop_column(u'method', 'performer')
    op.drop_column(u'method', 'hardware')
    op.drop_column(u'_metadata', 'description')
    op.drop_index(op.f('ix_rnaseqdataset_rnaseqexperiment_sample_id'), table_name='rnaseqdataset_rnaseqexperiment')
    op.drop_index(op.f('ix_rnaseqdataset_rnaseqexperiment_experiment_id'), table_name='rnaseqdataset_rnaseqexperiment')
    op.drop_table('rnaseqdataset_rnaseqexperiment')
    op.drop_table('rna_seq_experiment')
    op.drop_table('rna_seq_dataset')
    op.drop_index(op.f('ix__metadata_variable_variable_id'), table_name='_metadata_variable')
    op.drop_index(op.f('ix__metadata_variable__metadata_id'), table_name='_metadata_variable')
    op.drop_table('_metadata_variable')
    op.drop_index(op.f('ix__metadata_characteristic_characteristic_id'), table_name='_metadata_characteristic')
    op.drop_index(op.f('ix__metadata_characteristic__metadata_id'), table_name='_metadata_characteristic')
    op.drop_table('_metadata_characteristic')
    op.drop_table('variable')
    op.drop_table('characteristic')
    # ### end Alembic commands ###
