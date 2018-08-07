"""
Version:
"""

#%%
import atomica.ui as au
num_pops = 5
data_start = 2000
data_end = 2035
args = {"num_pops":int(num_pops), "data_start":int(data_start), "data_end":int(data_end)}
new_proj_name = 'foomico' # Get a unique name for the project to be added.
F = au.ProjectFramework(name=new_proj_name , inputs=au.atomica_path(['tests','frameworks'])+'framework_tb.xlsx')
proj = au.Project(framework=F, name=new_proj_name) # Create the project, loading in the desired spreadsheets.
file_name = '%s.xlsx' % proj.name # Create a filename containing the project name followed by a .prj suffix.
full_file_name = '%s' % (file_name) # Generate the full file name with path.
proj.create_databook(databook_path=full_file_name, **args) # Return the databook
