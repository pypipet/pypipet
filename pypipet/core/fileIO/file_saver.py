import pandas as pd
import yaml
import shutil


def write_csv_file(data:list, filename):
    df = pd.DataFrame(data)
    return df.to_csv(filename,
                index=False)


def _model_to_dict(obj):
    try:
        return obj.get_all_attrs()
    except Exception as e:
        print(e)

def write_yaml(data, filename):
    with open(filename, 'w') as outfile:
        yaml.dump(data, outfile)

def copy_file(src, dst):
    shutil.copyfile(src, dst)