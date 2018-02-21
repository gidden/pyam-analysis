import os

from pyam_analysis import IamDataFrame, plotting
from testing_utils import test_ia, here, data_path

import pytest
import pandas as pd
from numpy import testing as npt


def test_model(test_ia):
    assert test_ia['model'].model.unique() == ['test_model']


def test_scenario(test_ia):
    assert test_ia['scenario'].scenario.unique() == ['test_scenario']


def test_region(test_ia):
    assert test_ia['region'].region.unique() == ['World']


def test_variable(test_ia):
    assert list(test_ia['variable'].variable.unique()) == ['Primary Energy',
                                                           'Primary Energy|Coal']


def test_variable_depth(test_ia):
    obs = list(test_ia.filter({'level': 0})['variable'].variable.unique())
    exp = ['Primary Energy']
    assert obs == exp


def test_variable_unit(test_ia):
    dct = {'variable': ['Primary Energy', 'Primary Energy|Coal'],
           'unit': ['EJ/y', 'EJ/y']}
    cols = ['variable', 'unit']
    exp = pd.DataFrame.from_dict(dct)[cols]
    npt.assert_array_equal(test_ia[cols].drop_duplicates(), exp)


def test_timeseries(test_ia):
    dct = {'model': ['test_model'] * 2, 'scenario': ['test_scenario'] * 2,
           'years': [2005, 2010], 'value': [1, 6]}
    exp = pd.DataFrame(dct).pivot_table(index=['model', 'scenario'],
                                        columns=['years'], values='value')
    obs = test_ia.filter({'variable': 'Primary Energy'}).timeseries()
    npt.assert_array_equal(obs, exp)


def test_read_pandas():
    df = pd.read_csv(data_path)
    ia = IamDataFrame(df)
    assert list(ia['variable'].variable.unique()) == [
        'Primary Energy', 'Primary Energy|Coal']


def test_validate_pass(test_ia):
    assert test_ia.validate(criteria='Primary Energy', exclude=True) is None

    # make sure that the passed validation is NOT marked as excluded
    assert list(test_ia['exclude'].exclude) == [False]


def test_validate_fail(test_ia):
    dct = {'model': ['test_model'], 'scenario': ['test_scenario']}
    exp = pd.DataFrame(dct)[['model', 'scenario']]
    obs = test_ia.validate(criteria='Secondary Energy')
    npt.assert_array_equal(obs, exp)
    
    # make sure that the failed validation is NOT marked as excluded
    assert list(test_ia['exclude'].exclude) == [False]


def test_validate_exclude(test_ia):
    df = test_ia
    obs = df.validate(criteria='Secondary Energy', exclude=True)

    dct = {'model': ['test_model'], 'scenario': ['test_scenario']}
    exp = pd.DataFrame(dct)[['model', 'scenario']]
    npt.assert_array_equal(obs, exp)

    exp = exp.set_index(['model', 'scenario'])
    exp['exclude'] = True
    obs = test_ia['exclude']
    pd.testing.assert_frame_equal(obs, exp)


def test_category_none(test_ia):
    test_ia.categorize('category', 'Testing', {'Primary Energy': {'up': 0.8}})
    obs = test_ia['category']
    assert obs is None


def test_category_pass():
    df = IamDataFrame(data=data_path)
    dct = {'model': ['test_model'], 'scenario': ['test_scenario']}
    exp = pd.DataFrame(dct)[['model', 'scenario']]
    obs = df.categorize('category', 'Testing', {'Primary Energy': {'up': 10}},
                        color='red')
    npt.assert_array_equal(obs, exp)

    obs2 = df.metadata('Testing')
    npt.assert_array_equal(obs2[['model', 'scenario']], exp)


def test_load_metadata(test_ia):
    with pytest.warns(Warning) as record:
        test_ia.load_metadata(os.path.join(
            here, 'testing_metadata.xlsx'), sheet_name='metadata')
    assert len(record) == 1
    assert str(record[0].message) == 'overwriting 1 metadata entry'

    obs = test_ia.metadata()
    dct = {'model': ['test_model'], 'scenario': ['test_scenario'],
           'category': ['imported']}
    exp = pd.DataFrame(dct).set_index(['model', 'scenario'])
    npt.assert_array_equal(obs, exp)


def test_append():
    df = IamDataFrame(data=data_path)
    df2 = df.append(other=os.path.join(here, 'testing_data_2.csv'))
    assert df.scenarios() == ['test_scenario']
    assert df2.scenarios() == ['test_scenario', 'append_scenario']


def test_append_duplicates(test_ia):
    pytest.raises(ValueError, test_ia.append,
                  other=os.path.join(here, 'testing_data.csv'))


def test_interpolate():
    df = IamDataFrame(data=data_path)
    df.interpolate(2007)
    dct = {'model': ['test_model'] * 3, 'scenario': ['test_scenario'] * 3,
           'years': [2005, 2007, 2010], 'value': [1, 3, 6]}
    exp = pd.DataFrame(dct).pivot_table(index=['model', 'scenario'],
                                        columns=['years'], values='value')
    obs = df.filter({'variable': 'Primary Energy'}).timeseries()
    npt.assert_array_equal(obs, exp)
