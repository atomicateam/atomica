# -*- coding: utf-8 -*-
"""
Optima Core project-framework input/output file.
Contains functions to create, import and export framework files.
This is primarily referenced by the ProjectFramework object.
"""

from optimacore.system import logUsage, accepts, returns

import xlsxwriter as xw
import itertools as it



@logUsage
@accepts(str)
def createFrameworkTemplate(framework_path):
    """
    Creates a template framework Excel file.
    Returns True for process success.
    """
    framework_file = xw.Workbook(framework_path)
    format_bold = framework_file.add_format({'bold': True})
    fw_poptypes = framework_file.add_worksheet("Population Types")
    comment_width_scale = 3
    comment_height_scale = 3
    
    header_label = "Display Name"
    header_name = "Code Name"
    comment_prefix_label = "This column is for the 'display name' of"
    comment_suffix_label = ("Note: A display name is a representative label that users interface with (e.g. in databooks and plots). "
                            "It should be in title or sentence case.")
    comment_prefix_name = "This column is for the 'code name' of"
    comment_suffix_name = ("Note: A code name is a representative key that developers interface with (e.g. in scripts and the codebase). "
                           "It should be in lower case without spaces.")
    comment_poptype_classification = ("a relevant classification set for populations within the model, such as species, sex, coinfection status, etc.\n"
                                      "This classification should be distinct from any states of primary focus within a population 'cascade' network.")
    comment_poptype_category = ("a category within a classification set defined in previous columns for populations within the model.\n"
                                "If no classification was named on the same row, this category belongs to the classification defined in the nearest row above.\n"
                                "Examples may include human or mosquito for species, male or female for sex, HIV-infected or HIV-uninfected for coinfection status, etc.\n"
                                "There is no restriction on the number of categories per classification.")

    fw_poptypes_headers = [" ".join(a) for a in it.product(["Classification","Category"],[header_label,header_name])]
    fw_poptypes_comments = ["\n".join(b) for b in zip([" ".join(reversed(a)) for a in it.product([comment_poptype_classification,comment_poptype_category],
                                                                                                 [comment_prefix_label,comment_prefix_name])],
                                                      ["".join(a) for a in it.product(["",""],[comment_suffix_label,comment_suffix_name])])]
    
    for i in xrange(len(fw_poptypes_headers)):
        header_width = len(fw_poptypes_headers[i])
        comment_length = len(fw_poptypes_comments[i])
        fw_poptypes.write(0, i, fw_poptypes_headers[i], format_bold)
        fw_poptypes.write_comment(0, i, fw_poptypes_comments[i], 
                                  {'x_scale': comment_width_scale, 'y_scale': comment_height_scale})
        fw_poptypes.set_column(i, i, header_width)

    return
    