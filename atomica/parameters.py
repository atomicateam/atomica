#%% Imports

from atomica.system import AtomicaException, logger
from atomica.structure_settings import DatabookSettings as DS
from atomica.interpolation import interpolateFunc
#from optima_tb.databook import getEmptyData
#from optima_tb.settings import DO_NOT_SCALE, DEFAULT_YFACTOR
from sciris.core import odict, uuid

from copy import deepcopy as dcp
import numpy as np
#from csv import reader, writer
import operator



#%% Parameter class that stores one array of values converted from raw project data

class Parameter(object):
    """ Class to hold one set of parameter values disaggregated by populations. """
    
    def __init__(self, name, t = None, y = None, y_format = None, y_factor = None, autocalibrate = None):
        self.name = name
        
        # These ordered dictionaries have population names as keys.
        if t is None: t = odict()
        if y is None: y = odict()
        if y_format is None: y_format = odict()
        if y_factor is None: y_factor = odict()
        if autocalibrate is None: autocalibrate = odict()
        self.t = t # Time data 
        self.y = y # Value data
        self.y_format = y_format                # Value format data (e.g. Probability, Fraction or Number).
        self.y_factor = y_factor                # Scaling factor of data. Corresponds to different transformations whether format is fraction or number.
        self.autocalibrate = autocalibrate      # A set of boolean flags corresponding to y_factor that denote whether this parameter can be autocalibrated.
                                                                
    def insertValuePair(self, t, y, pop_name):
        """ Check if the inserted t value already exists for the population parameter. If not, append y value. If so, overwrite y value. """
        # Make sure it stays sorted
        if t in self.t[pop_name]:
            self.y[pop_name][self.t[pop_name]==t] = y
        else:
            idx = np.searchsorted(self.t[pop_name],t)
            self.t[pop_name] = np.insert(self.t[pop_name],idx,t)
            self.y[pop_name] = np.insert(self.y[pop_name],idx,y)

    def removeValueAt(self, t, pop_name):
        """ Remove value at time point 't' and the time point itself if no other time point exists. """

        if t in self.t[pop_name]:
            if len(self.t[pop_name]) <= 1:
                return False
            else:
                idx = (self.t[pop_name]==t).nonzero()[0][0]
                self.t[pop_name] = np.delete(self.t[pop_name], idx)
                self.y[pop_name] = np.delete(self.y[pop_name], idx)
                return True
        else:
            return True

    def removeBetween(self, t_remove, pop_name):
        # t is a two element vector [min,max] such that
        # times > min and < max are removed
        # Note that the endpoints are not included!
        original_t = self.t[pop_name]
        for tval in original_t:
            if tval > t_remove[0] and tval < t_remove[1]:
                self.removeValueAt(tval,pop_name)
        
    def interpolate(self, tvec = None, pop_name = None):#, extrapolate_nan = False):
        """ Take parameter values and construct an interpolated array corresponding to the input time vector. """
        
        # Validate input.
        if pop_name not in self.t.keys(): raise AtomicaException("ERROR: Cannot interpolate parameter '{0}' without referring to a proper population name.".format(pop_name))
        if tvec is None: raise AtomicaException("ERROR: Cannot interpolate parameter '{0}' without providing a time vector.".format(self.name))
        if not len(self.t[pop_name]) > 0: raise AtomicaException("ERROR: There are no timepoint values for parameter '{0}', population '{1}'.".format(self.name, pop_name))
        if not len(self.t[pop_name]) == len(self.y[pop_name]): raise AtomicaException("ERROR: Parameter '{0}', population '{1}', does not have corresponding values and timepoints.".format(self.name, pop_name))

#        if len(self.t[pop_name]) == 1 and not extrapolate_nan:
#            output = np.ones(len(tvec))*(self.y[pop_name][0]*np.abs(self.y_factor[pop_name]))   # Don"t bother running interpolation loops if constant. Good for performance.
#        else:
        input_t = dcp(self.t[pop_name])
        input_y = dcp(self.y[pop_name])#*np.abs(self.y_factor[pop_name])
        
        # Eliminate np.nan from value array before interpolation. Makes sure timepoints are appropriately constrained.
        cleaned_times = input_t[~np.isnan(input_y)] # NB. numpy advanced indexing here results in a copy
        cleaned_vals = input_y[~np.isnan(input_y)]

        if len(cleaned_times) == 0: # If there are no timepoints after cleaning, this may be a calculated parameter.
            output = np.ones(len(tvec)) * np.nan
        elif len(cleaned_times) == 1:  # If there is only one timepoint, corresponding cost and cov values should be real valued after loading databook. But can double-validate later.
            output = np.ones(len(tvec)) * (cleaned_vals)[0]  # Don't bother running interpolation loops if constant. Good for performance.
        else:
            # Pad the input vectors for interpolation with minimum and maximum timepoint values, to avoid extrapolated values blowing up.
            ind_min, t_min = min(enumerate(cleaned_times), key=lambda p: p[1])
            ind_max, t_max = max(enumerate(cleaned_times), key=lambda p: p[1])
            val_at_t_min = cleaned_vals[ind_min]
            val_at_t_max = cleaned_vals[ind_max]

            # This padding effectively keeps edge values constant for desired time ranges larger than data-provided time ranges.
            if tvec[0] < t_min:
                cleaned_times = np.append(tvec[0], cleaned_times)
                cleaned_vals = np.append(val_at_t_min, cleaned_vals)
            if tvec[-1] > t_max:
                cleaned_times = np.append(cleaned_times, tvec[-1])
                cleaned_vals = np.append(cleaned_vals, val_at_t_max)

            output = interpolateFunc(cleaned_times, cleaned_vals, tvec)
            
#            if not extrapolate_nan:
#                # Pad the input vectors for interpolation with minimum and maximum timepoint values, to avoid extrapolated values blowing up.
#                ind_min, t_min = min(enumerate(self.t[pop_name]), key = lambda p: p[1])
#                ind_max, t_max = max(enumerate(self.t[pop_name]), key = lambda p: p[1])
#                y_at_t_min = self.y[pop_name][ind_min]
#                y_at_t_max = self.y[pop_name][ind_max]
#                
#                # This padding effectively keeps edge values constant for desired time ranges larger than data-provided time ranges.
#                if tvec[0] < t_min:
#                    input_t = np.append(tvec[0], input_t)
#                    input_y = np.append(y_at_t_min, input_y)
#                if tvec[-1] > t_max:
#                    input_t = np.append(input_t, tvec[-1])
#                    input_y = np.append(input_y, y_at_t_max)
#            
#            elif len(input_t) == 1:       # The interpolation function currently complains about single data points, so this is the simplest hack for nan extrapolation.
#                input_t = np.append(input_t, input_t[-1] + 1e-12)
#                input_y = np.append(input_y, input_y[-1])
#            
#            output = interpolateFunc(x = input_t, y = input_y, xnew = tvec, extrapolate_nan = extrapolate_nan)
        
        return output
    
    def __repr__(self, *args, **kwargs):
        return "Parameter: {0}\n\nt\n{1}\ny\n{2}\ny_format\n{3}\ny_factor\n{4}\n".format(self.name,self.t,self.y,self.y_format,self.y_factor)
        

#%% Parset class that contains one set of parameters converted from raw project data

class ParameterSet(object):
    """ Class to hold all parameters. """
    
    def __init__(self, name = "default"):
        self.name = name 
        self.uid = uuid()

        self.pop_names = []         # List of population names.
                                    # Names are used throughout the codebase as variable names (technically dict keys).
        self.pop_labels = []        # List of population labels.
                                    # Labels are used only for user interface and can be more elaborate than simple names.
        self.pars = odict()
        self.pars["cascade"] = []
        self.pars["comps"] = []
        self.pars["characs"] = []
        self.par_ids = {"cascade":{}, "comps":{}, "characs":{}}
        
        self.transfers = odict()    # Dictionary of inter-population transitions.
        self.contacts = odict()     # Dictionary of inter-population interaction weights.
        
        logger.info("Created ParameterSet: {0}".format(self.name))
        
    def change_id(self, new_name = None):
        """
        Change the name and uid of this parameter set.
        This is a dangerous function that could break references by uid, so should only be used on duplicates.
        """
        new_name_string = ""
        if not new_name is None: 
            if new_name == self.name:
                logger.warning("A parameter set with name '{0}' has been explicitly requested to rename itself '{0}'".format(new_name))
            self.name = new_name
            new_name_string = "with name '{0}' ".format(new_name)
        logger.warning("A parameter set {0}has been given a new uid.".format(new_name_string))

    def set_scaling_factor(self,par_name,pop_name,scale):
        par = self.getPar(par_name)
        par.y_factor[pop_name] = scale

    def getPar(self, name):
        for par_type in ["cascade","comps","characs"]:
            if name in self.par_ids[par_type].keys():
                return self.pars[par_type][self.par_ids[par_type][name]]
        raise AtomicaException("ERROR: Name '{0}' cannot be found in parameter set '{1}' as either a cascade parameter, compartment or characteristic.".format(name, self.name))
    
    def makePars(self, data):
        self.pop_names = data.specs[DS.KEY_POPULATION].keys()
        self.pop_labels = [data.getSpec(pop_name)["label"] for pop_name in self.pop_names]
            
        # Cascade parameter and characteristic extraction.
        for k in range(3):
            item_key = [DS.KEY_PARAMETER, DS.KEY_COMPARTMENT, DS.KEY_CHARACTERISTIC][k]
            item_group = ["cascade","comps","characs"][k]
            for l, name in enumerate(data.specs[item_key]):
                self.par_ids[item_group][name] = l
                self.pars[item_group].append(Parameter(name = name))
                popdata = data.getSpecValue(name, DS.TERM_DATA)
                for pop_id in popdata.keys():
                    tvec,yvec = popdata.getArrays(pop_id)

                    # TODO: Deal with assumptions in a better way by storing them regardless under assumption attribute.
                    #       For now, convert assumption from None to year 0 if no other values exist, otherwise delete assumption index (its value should have been ignored during data import).
#                    if tvec[0] is None:
#                        if len(tvec) == 1: tvec[0] = 0.0
#                    else: 
#                        del tvec[0]
#                        del yvec[0]
                    self.pars[item_group][-1].t[pop_id] = tvec
                    self.pars[item_group][-1].y[pop_id] = yvec
                    self.pars[item_group][-1].y_format[pop_id] = popdata.getFormat(pop_id)
                    self.pars[item_group][-1].y_factor[pop_id] = 1.0 # TODO - maybe read this in from the databook later?

#                self.pars["cascade"][-1].y_format[pop_id] = data[DS.KEY_PARAMETER][name][pop_id]["y_format"]
#                if data[DS.KEY_PARAMETER][name][pop_id]["y_factor"] == DO_NOT_SCALE:
#                    self.pars["cascade"][-1].y_factor[pop_id] = DEFAULT_YFACTOR
#                    self.pars["cascade"][-1].autocalibrate[pop_id] = False
#                else:
#                    self.pars["cascade"][-1].y_factor[pop_id] = data[DS.KEY_PARAMETER][name][pop_id]["y_factor"]
#                    self.pars["cascade"][-1].autocalibrate[pop_id] = True
                
#        # Characteristic parameters (e.g. popsize/prevalence).
#        # Despite being mostly data to calibrate against, is still stored in full so as to interpolate initial value.
#        for l, name in enumerate(data.specs[DS.KEY_CHARACTERISTIC]):
#            self.par_ids["characs"][name] = l
#            self.pars["characs"].append(Parameter(name = name))
#            for pop_id in data.getSpecValue(name, DS.TERM_DATA):
#                self.pars["characs"][l].t[pop_id] = data.getSpecValue(name, DS.TERM_DATA)[pop_id]["t"]
#                self.pars["characs"][l].y[pop_id] = data.getSpecValue(name, DS.TERM_DATA)[pop_id]["y"]
##                self.pars["characs"][l].y_format[pop_id] = data.getSpec(name)[DS.TERM_VALUE][pop_id]["y_format"]
##                if data[DS.KEY_CHARACTERISTIC][name][pop_id]["y_factor"] == DO_NOT_SCALE:
##                    self.pars["characs"][-1].y_factor[pop_id] = DEFAULT_YFACTOR
##                    self.pars["characs"][-1].autocalibrate[pop_id] = False
##                else:
##                    self.pars["characs"][-1].y_factor[pop_id] = data[DS.KEY_CHARACTERISTIC][name][pop_id]["y_factor"]
##                    self.pars["characs"][-1].autocalibrate[pop_id] = True
            
#        # Migrations, including aging.
#        for trans_type in data["transfers"].keys():
#            if trans_type not in self.transfers: self.transfers[trans_type] = odict()
#            
#            for source in data["transfers"][trans_type].keys():
#                if source not in self.transfers[trans_type]: self.transfers[trans_type][source] = Parameter(name = trans_type + "_from_" + source)
#                for target in data["transfers"][trans_type][source].keys():
#                    self.transfers[trans_type][source].t[target] = data["transfers"][trans_type][source][target]["t"]
#                    self.transfers[trans_type][source].y[target] = data["transfers"][trans_type][source][target]["y"]
#                    self.transfers[trans_type][source].y_format[target] = data["transfers"][trans_type][source][target]["y_format"]
#                    self.transfers[trans_type][source].y_factor[target] = data["transfers"][trans_type][source][target]["y_factor"]
#                    
#        self.contacts = dcp(data["contacts"])   # Simple copying of the contacts structure into data. No need to be an object.
    
    
#    def inflate(self,tvec):
#        """
#        Inflates cascade parameters only
#        
#        """
#        for (id,par) in enumerate(self.pars["cascade"]):
#           
#            for j,pop_name in enumerate(self.pop_names):        
#                self.pars["cascade"][id].y[j] = par.interpolate(tvec = tvec, pop_name = pop_name)
#                self.pars["cascade"][id].t[j] = tvec
#           
#    
#    def __getMinMax(self,y_format):
#        if y_format.lower() == "fraction":
#            return (0.,1.)
#        elif y_format.lower() in ["number","proportion"]:
#            return (0.,np.inf)
#        else:
#            raise AtomicaException("Unknown y_format '{0}' encountered while returning min-max bounds".format(y_format))
#    
#    
#    def extract(self,settings=None,getMinMax=False,getYFactor=False):
#        """
#        Extract parameters values into a list
#        
#        Note that this method is expecting one y-value per parameter, and does 
#        not allow for time-varying parameters. If time-varying parameters are expected, then 
#        getYFactor will return the scaling factor (y_factor) that can be used to manipulate
#        
#        To avoid values from being extracted, users should use the assumption value to specify values, or 
#        mark the "Autocalibrate" column in the cascade spreadsheet with "-1" (== settings.DO_NOT_SCALE value)
#        
#        Note that parameters defined as functions will not be extracted.
#        
#        If getMinMax=True, this function additionally returns the min and max values for each of the parameters returned,
#        depending on y_format. Each minmax value is a tuple of form (min,max). Note that min/max values can be either a float, int, or None.
#        
#        Params:
#            getMinMax     boolean. Additionally return min and max values for each of the parameters returned in format: 
#                            @TODO: document format for this and return statements
#            getYFactor    boolean: 
#                            
#        Return:
#            paramvec
#            minmax        minmax values. [] if getMinMax was False, else a list of tuples: [(min,max)]
#            casc_names    
#        """    
##        import optima_tb.settings as settings 
#        
#        paramvec = [] # Not efficient - would prefer: np.zeros(len(self.pop_names)*len(self.pars["cascade"]))
#        minmax = []
#        casc_names = []
#        index= 0
#        for pop_id in self.pop_names:
#            #for (j,casc_id) in enumerate(self.par_ids["cascade"]): 
#            for (casc_id,j) in sorted(self.par_ids["cascade"].items(), key=operator.itemgetter(1)):
##                print casc_id
##                print j
#
#                # Do not extract parameters that are functions (if settings are available) or otherwise marked not to be calibrated.
#                if self.pars["cascade"][j].autocalibrate[pop_id] == False or (not settings is None and casc_id in settings.par_funcs):
#                    continue
#                #paramvec[index] = [self.pars["cascade"][j].y[pop_id]]
#                if getYFactor:
#                    paramvec.append(self.pars["cascade"][j].y_factor[pop_id])
#                else:
#                    paramvec.append(self.pars["cascade"][j].y[pop_id])
#                    
#                if getMinMax:
#                    minmax_bounds = self.__getMinMax(self.pars["cascade"][j].y_format[pop_id])
#                    if getYFactor and minmax_bounds[1] is not None:
#                        # use the bounds to calculate the corresponding minmax values for the bounds: 
##                        # possibilities are (0.,1.) for fraction, and (0,None) for number and proportion.
##                        # - yfactor-min has to remain 0, so leave
##                        yval_max= np.max(self.pars["cascade"][j].y[pop_id])
##                        if yval_max == 0:
##                            logger.info("ParameterSet: max value of 0 observed for fraction for casc_id=%s"%casc_id)
##                            yval_max = settings.TOLERANCE
##                        tmp_upper = minmax_bounds[1]
##                        tmp_upper /= yval_max
##                        minmax_bounds = (minmax_bounds[0], tmp_upper)
#                        minmax_bounds = (0., np.inf)      # There is probably no reason to enforce bounds on y_factor in this layer as fraction ranges are handled in model.py.
#                    # if we"re grabbing the minmax values for the y-values directly, then use the values
#                    minmax.append(minmax_bounds)
#                    # also grab the cascade names for debugging and logging purposes
#                    casc_names.append((casc_id,pop_id))
#                index+=1
#                
#        if getMinMax:
#            return paramvec,minmax,casc_names
#        
#        return paramvec,None,casc_names 
#    
#    def extractEntryPoints(self,proj_settings,useInitCompartments=False):
#        """
#        Extract initial compartments: 
#        """
#        import optima_tb.settings as settings
#        
#        init_compartments = []
#        charac_names = []
#        if useInitCompartments:
#            for pop_id in self.pop_names:
#                for (charac_id,j) in sorted(self.par_ids["characs"].items(), key=operator.itemgetter(1)):
#                    #if "entry_point" in proj_settings.charac_specs[charac_id].keys() and self.pars["characs"][j].y_factor[pop_id] != settings.DO_NOT_SCALE:
##                    print charac_id
##                    print j
#                    if "entry_point" in proj_settings.charac_specs[charac_id].keys() and self.pars["characs"][j].autocalibrate[pop_id] == True:
#                        init_compartments.append(self.pars["characs"][j].y_factor[pop_id])
#                        charac_names.append((charac_id,pop_id))                        
#        return init_compartments,charac_names
#         
#    
#    def update(self, par_vec, par_pop_names, isYFactor=False):
#        """
#        Update parameters from a list of values, given a corresponding list of parameter names and population names, arranged in pairs.
#
#        TODO: extend function so that can also add years or format values
#        TODO: remove index ...?
#        """
#        import optima_tb.settings as settings
#        
#        index = 0
#        for par_pop_name in par_pop_names:
#            par_name = par_pop_name[0]
#            pop_name = par_pop_name[1]
#            par = self.getPar(par_name)    # Returns a parameter or characteristic as required.        
#                
#            if isYFactor:
#                
##                if par.autocalibrate[pop_name]:
##                    logger.info("ParameterSet %s is acknowledging that it can calibrate the y-factor for parameter %s, population %s." % (self.name, par_name, pop_name))
##                else:
##                    logger.info("ParameterSet %s has not modifed its y-factor value for parameter %s, population %s, due to y-factor constraints." % (self.name, par_name, pop_name))
##                    continue
#                
#                if par.y_factor[pop_name] != par_vec[index]:
#                    logger.info("ParameterSet '{0}' is updating its y-factor for parameter '{1}', population '{2}' from '{3}' to '{4}'.".format(self.name, par_name, pop_name, par.y_factor[pop_name], par_vec[index]))
#                
#                par.y_factor[pop_name] = par_vec[index]
#            else:
#                par.y[pop_name] = par_vec[index]
#            index += 1
#            
#        
##        index = 0
##        for (i,pop_id) in enumerate(self.pop_names):
##            #for (j,casc_id) in enumerate(self.par_ids["cascade"]): 
##            for (casc_id,j) in sorted(self.par_ids["cascade"].items(), key=operator.itemgetter(1)):
##                # perform checks
##                if self.pars["cascade"][j].y_factor[pop_id] == settings.DO_NOT_SCALE:
##                    continue
##                if not isYFactor and len(self.pars["cascade"][j].y[pop_id]) != len(paramvec[index]):
##                    raise AtomicaException("Could not update parameter set "%s" for pop=%s,cascade=%s as updated parameter has different length."%(self.name,pop_id,casc_id))
##                # update y or y_factor, based on parameters
##                if isYFactor:
##                    self.pars["cascade"][j].y_factor[pop_id] = paramvec[index]
##                else:
##                    self.pars["cascade"][j].y[pop_id] = paramvec[index]
##                # finally, update index count
##                index += 1
#                
#        logger.info("Updated ParameterSet '{0}' with new values.".format(self.name))
#    
##    def updateEntryPoints(self,proj_settings,compartment_t0,charac_names):
##        """
##        
##        
##        """
##        import optima_tb.settings as settings 
##        
##        index = 0 
##        for pop_id in self.pop_names:
##            for (charac_id,j) in sorted(self.par_ids["characs"].items(), key=operator.itemgetter(1)):
##                if "entry_point" in proj_settings.charac_specs[charac_id].keys() and self.pars["characs"][j].y_factor[pop_id] != settings.DO_NOT_SCALE:
##                    if charac_names[index] == charac_id:
##                        self.pars["characs"][j].y_factor[pop_id]= compartment_t0[index]
##                        #self.pars["characs"][j].y[pop_id][0] *= compartment_t0[index]
##                        #print "initial for %s is %g"%(charac_id,self.pars["characs"][j].y[pop_id][0] )
##                        index += 1
##                    else:
##                        logger.debug("Updating entry points: characteristic name for entry point doesn"t match updated value [%s,%s]"%(charac_names[index],charac_id))
#                        
#        
#    #TODO: Fix as the DO_NOT_SCALE setting no longer represents an absence of rescaling; attribute autocalibrate does.
#    def _updateFromYFactor(self):
#        """
#        Goes through each of the cascade parameters and updates the y-values to be
#        y-value*y_factor. This is used for example in autocalibration (which can scale y_factor),
#        which may have set the y_factor to a non-unary value but then needs to update y values at the end. 
#        
#        The purpose of doing this is to ensure that y_values are correct, if inspected, to avoid errors if a process
#        only checks y_value rather than y_value*y_factor.
#        
#        """
#        import optima_tb.settings as settings
#        
#        for (i,pop_id) in enumerate(self.pop_names):
#            for (j,casc_id) in enumerate(self.par_ids["cascade"]): 
#                if self.pars["cascade"][j].y_factor[pop_id] == settings.DO_NOT_SCALE:
#                    continue
#                self.pars["cascade"][j].y[pop_id] *= self.pars["cascade"][j].y_factor[pop_id] 
#                self.pars["cascade"][j].y_factor[pop_id] = 1.0
#                
#        for pop_id in self.pop_names:
#            for (charac_id,j) in sorted(self.par_ids["characs"].items(), key=operator.itemgetter(1)):
#                if self.pars["characs"][j].y_factor[pop_id] == settings.DO_NOT_SCALE:
#                    continue
#                self.pars["characs"][j].y[pop_id] *= self.pars["characs"][j].y_factor[pop_id] 
#                self.pars["characs"][j].y_factor[pop_id] = 1.0
#        
#        
#        
#    
#    def __repr__(self, *args, **kwargs):
#        return "ParameterSet: '{0}' \npars: \n'{1}'".format(self.name, self.pars) 
#    
#    
#    def __add__(a,b):
#        """
#        Add two parameter sets together, with the value of any parameter
#        cascade in ParameterSet "b" being added to the corresponding value 
#        in ParameterSet "a". If no corresponding value in a exists, it is inserted.
#        
#        As only the cascade values in "b" are copied over, it is mandatory at this
#        stage that "a" should be the ParameterSet kept for it"s characteristics and
#        transfer definitions.
#        
#        Throws an AtomicaException if parameters with matching names have different
#        y_formats
#        
#        Usage:
#        default  = ParameterSet()
#        largeVal = ParameterSet()
#        c = default + largeVal
#        print type(c)
#        > "ParameterSet"
#        
#        """
#        logger.debug("Adding two parameter sets together: '{0}' + '{1}'".format(a.name,b.name))
#        c = dcp(a)
#        for par_name, b_index in b.par_ids["cascade"].iteritems():
#            
#            # find corresponding par_id in c
#            c_index = c.par_ids["cascade"][par_name]
#            # for each population referenced:
#            for pop in b.pars["cascade"][b_index].t.keys():     
#                # check that the y_format matches: if not, throw an error
#                if b.pars["cascade"][b_index].y_format[pop] != c.pars["cascade"][c_index].y_format[pop]:
#                    raise AtomicaException("ERROR: trying to combine two Parameters with different y_formats: ")
#                # add or insert value of b into c
#                for i,t_val in enumerate(b.pars["cascade"][b_index].t[pop]):
#                    
#                    tmp =  c.pars["cascade"][c_index].t[pop]
#                    if t_val in c.pars["cascade"][c_index].t[pop]: 
#                        mask = tmp == t_val
#                        c.pars["cascade"][c_index].y[pop][mask] += b.pars["cascade"][b_index].y[pop][i]
#                    else:
#                        c.pars["cascade"][c_index].y[pop] = np.append(c.pars["cascade"][c_index].y[pop],[b.pars["cascade"][b_index].y[pop][i]])
#                        c.pars["cascade"][c_index].t[pop] = np.append(c.pars["cascade"][c_index].t[pop],[t_val])
#                
#                # correct for min/max, based on format type: as presumably "a" was already correct, 
#                # we only need to check that the min max wasn"t violated when we"re adding values together, and therefore
#                # only have to check when we"ve added something from b. 
#                minmax = c.__getMinMax(a.pars["cascade"][c_index].y_format[pop])
#                if minmax[0] is not None and sum(c.pars["cascade"][c_index].y[pop]<minmax[0]) > 0: 
#                    logger.debug("ParameterSet.__add__ : Observed min that is less than accepted min value for parameter type '{0}': cascade name='{1}' for population='{2}'".format(c.pars["cascade"][c_index].y_format[pop],par_name,pop))
#                    c.pars["cascade"][c_index].y[pop][c.pars["cascade"][c_index].y[pop]<minmax[0]] = minmax[0]
#                if minmax[1] is not None and sum(c.pars["cascade"][c_index].y[pop]>minmax[1]) > 0: 
#                    logger.debug("ParameterSet.__add__ : Observed max that is less than accepted max value for parameter type '{0}': cascade name='{1}' for population='{2}'".format(c.pars["cascade"][c_index].y_format[pop],par_name,pop))
#                    c.pars["cascade"][c_index].y[pop][c.pars["cascade"][c_index].y[pop]>minmax[1]] = minmax[1]
#        return c
 
    

#"""
#This module defines the Parameters classes, which are used for single parameters,
#and the Parameterset class, which is for the full set of parameters.
#
#Version: 2018mar27
#"""
#
#from atomica.system import AtomicaException # CK: this should be renamed
#from atomica.project_settings import convertlimits, gettvecdt
#from sciris.utils import odict, Link, today, defaultrepr, getdate, isnumber, printv, smoothinterp, getvaliddata, sanitize, findinds, inclusiverange, promotetolist, dcp
#from numpy import array, zeros, isnan, nan, isfinite, median, shape
#
#defaultsmoothness = 1.0 # The number of years of smoothing to do by default
#
##################################################################################################################################
#### Define the parameter set
##################################################################################################################################
#
#class Parameterset(object):
#    """ Class to hold all parameters and information on how they were generated, and perform operations on them"""
#    
#    def __init__(self, name="default", project=None, start=None, end=None):
#        self.name = name # Name of the parameter set, e.g. "default"
#        self.projectref = Link(project) # Store pointer for the project, if available
#        self.created = today() # Date created
#        self.modified = today() # Date modified
#        self.pars = None
#        self.popkeys = [] # List of populations
#        self.start = start # Start data
#        self.end = end # Enddata
#        
#    
#    def __repr__(self):
#        """ Print out useful information when called"""
#        output  = defaultrepr(self)
#        output += "Parameter set name: %s\n"    % self.name
#        output += "      Date created: %s\n"    % getdate(self.created)
#        output += "     Date modified: %s\n"    % getdate(self.modified)
#        output += "============================================================\n"
#        return output
#    
#    
#    def getresults(self, die=True):
#        """ Method for getting the results """
#        pass
#   
#    
#    def parkeys(self):
#        """ Return a list of the keys in pars that are actually parameter objects """
#        parslist = []
#        for key,par in self.pars.items():
#            if issubclass(type(par), Par):
#                parslist.append(key)
#        return parslist
#    
#    
#    def makepars(self, data=None, framework=None, fix=True, verbose=2, start=None, end=None):
#        """Method to make the parameters from data"""
#        
#        self.popkeys = data.specs["pop"].keys() # Store population keys more accessibly
#        self.pars = makepars(data=data.specs, framework=framework, verbose=verbose) # Initialize as list with single entry
#
#        return None
#
#
#
#    def interp(self, keys=None, start=None, end=2030, dt=0.2, tvec=None, smoothness=20, asarray=True, samples=None, verbose=2):
#        """ Prepares model parameters to run the simulation. """
#        printv("Making model parameters...", 1, verbose),
#        return None
#    
#    
#    def printpars(self, output=False):
#        outstr = ""
#        count = 0
#        for par in self.pars.values():
#            if hasattr(par,"p"): print("WARNING, population size not implemented!")
#            if hasattr(par,"y"):
#                if hasattr(par.y, "keys"):
#                    count += 1
#                    if len(par.keys())>1:
#                        outstr += "%3i: %s\n" % (count, par.name)
#                        for key in par.keys():
#                            outstr += "     %s = %s\n" % (key, par.y[key])
#                    elif len(par.keys())==1:
#                        outstr += "%3i: %s = %s\n\n" % (count, par.name, par.y[0])
#                    elif len(par.keys())==0:
#                        outstr += "%3i: %s = (empty)" % (count, par.name)
#                    else:
#                        print("WARNING, not sure what to do with %s: %s" % (par.name, par.y))
#                else:
#                    count += 1
#                    outstr += "%3i: %s = %s\n\n" % (count, par.name, par.y)
#        print(outstr)
#        if output: return outstr
#        else: return None
#
#
#    def listattributes(self):
#        """ Go through all the parameters and make a list of their possible attributes """
#        
#        maxlen = 20
#        pars = self.pars
#        
#        print("\n\n\n")
#        print("CONTENTS OF PARS, BY TYPE:")
#        partypes = []
#        for key in pars: partypes.append(type(pars[key]))
#        partypes = set(partypes)
#        count1 = 0
#        count2 = 0
#        for partype in set(partypes): 
#            count1 += 1
#            print("  %i..%s" % (count1, str(partype)))
#            for key in pars:
#                if type(pars[key])==partype:
#                    count2 += 1
#                    print("      %i.... %s" % (count2, str(key)))
#        
#        print("\n\n\n")
#        print("ATTRIBUTES:")
#        attributes = {}
#        for key in self.parkeys():
#            theseattr = pars[key].__dict__.keys()
#            for attr in theseattr:
#                if attr not in attributes.keys(): attributes[attr] = []
#                attributes[attr].append(getattr(pars[key], attr))
#        for key in attributes:
#            print("  ..%s" % key)
#        print("\n\n")
#        for key in attributes:
#            count = 0
#            print("  ..%s" % key)
#            items = []
#            for item in attributes[key]:
#                try: 
#                    string = str(item)
#                    if string not in items: 
#                        if len(string)>maxlen: string = string[:maxlen]
#                        items.append(string) 
#                except: 
#                    items.append("Failed to append item")
#            for item in items:
#                count += 1
#                print("      %i....%s" % (count, str(item)))
#        return None
#
#
#
#
##################################################################################################################################
#### Define the Parameter class
##################################################################################################################################
#
#class Par(object):
#    """
#    The base class for epidemiological model parameters.
#    Version: 2018mar23
#    """
#    def __init__(self, short=None, name=None, limits=(0.,1.), by=None, manual="", fromdata=None, m=1.0, prior=None, verbose=None, **defaultargs): # "type" data needed for parameter table, but doesn"t need to be stored
#        self.short = short # The short used within the code 
#        self.name = name # The full name, e.g. "HIV testing rate"
#        self.limits = limits # The limits, e.g. (0,1) -- a tuple since immutable
#        self.by = by # Whether it"s by population, partnership, or total
#        self.manual = manual # Whether or not this parameter can be manually fitted: options are "", "meta", "pop", "exp", etc...
#        self.fromdata = fromdata # Whether or not the parameter is made from data
#        self.m = m # Multiplicative metaparameter, e.g. 1
#        self.msample = None # The latest sampled version of the metaparameter -- None unless uncertainty has been run, and only used for uncertainty runs 
#    
#    def __repr__(self):
#        """ Print out useful information when called"""
#        output = defaultrepr(self)
#        return output
#    
#
#class Timepar(Par):
#    """ The definition of a single time-varying parameter, which may or may not vary by population """
#    
#    def __init__(self, t=None, y=None, **defaultargs):
#        Par.__init__(self, **defaultargs)
#        if t is None: t = odict()
#        if y is None: y = odict()
#        self.t = t # Time data, e.g. [2002, 2008]
#        self.y = y # Value data, e.g. [0.3, 0.7]
#    
#    def keys(self):
#        """ Return the valid keys for using with this parameter """
#        return self.y.keys()
#    
#    def sample(self, randseed=None):
#        """ Recalculate msample """
#        return None
#    
#    def interp(self, tvec=None, dt=None, smoothness=None, asarray=True, sample=None, randseed=None):
#        """ Take parameters and turn them into model parameters """
#        
#        # Validate input
#        if tvec is None: 
#            errormsg = "Cannot interpolate parameter "%s" with no time vector specified" % self.name
#            raise AtomicaException(errormsg)
#        tvec, dt = gettvecdt(tvec=tvec, dt=dt) # Method for getting these as best possible
#        if smoothness is None: smoothness = int(defaultsmoothness/dt) # Handle smoothness
#        
#        # Figure out sample
#        if not sample:
#            m = self.m
#        else:
#            if sample=="new" or self.msample is None: self.sample(randseed=randseed) # msample doesn"t exist, make it
#            m = self.msample
#        
#        # Set things up and do the interpolation
#        npops = len(self.keys())
#        if self.by=="pship": asarray= False # Force odict since too dangerous otherwise
#        if asarray: output = zeros((npops,len(tvec)))
#        else: output = odict()
#        for pop,key in enumerate(self.keys()): # Loop over each population, always returning an [npops x npts] array
#            yinterp = m * smoothinterp(tvec, self.t[pop], self.y[pop], smoothness=smoothness) # Use interpolation
#            yinterp = applylimits(par=self, y=yinterp, limits=self.limits, dt=dt)
#            if asarray: output[pop,:] = yinterp
#            else:       output[key]   = yinterp
#        if npops==1 and self.by=="tot" and asarray: return output[0,:] # npops should always be 1 if by==tot, but just be doubly sure
#        else: return output
#
#
#
##################################################################################################################################
#### Define methods to turn data into parameters
##################################################################################################################################
#
#
#def data2timepar(parname=None, data=None, keys=None, defaultind=0, verbose=2, **defaultargs):
#    """ Take data and turn it into default parameters"""
#    # Check that at minimum, name and short were specified, since can"t proceed otherwise
##    import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
#    try: 
#        name, short = defaultargs["label"], parname
#    except: 
#        errormsg = "Cannot create a time parameter without name and label."
#        raise AtomicaException(errormsg)
#        
#    par = Timepar(m=1.0, y=odict(), t=odict(), **defaultargs) # Create structure
#    par.name = name
#    par.short = short
#    for key in keys:
#        par.y[key] = data["values"].getValue(key)
#        if data["values"].getValue("t") is not None: # TODO this whole thing only works for constants... need to revamp data storage
#            par.t[key] = data["values"].getValue("t")
#        else:
#            par.t[key] = 2018. # TODO, remove this, it"s SUPER TEMPORARY -- a way to assign a year to constants/assumptions
#
##    for row,key in enumerate(keys):
##        try:
##            validdata = ~isnan(data[short][row]) # WARNING, this could all be greatly simplified!!!! Shouldn"t need to call this and sanitize()
##            par.t[key] = getvaliddata(data["years"], validdata, defaultind=defaultind) 
##            if sum(validdata): 
##                par.y[key] = sanitize(data[short][row])
##            else:
##                printv("data2timepar(): no data for parameter "%s", key "%s"" % (name, key), 3, verbose) # Probably ok...
##                par.y[key] = array([0.0]) # Blank, assume zero -- WARNING, is this ok?
##                par.t[key] = array([0.0])
##        except:
##            errormsg = "Error converting time parameter "%s", key "%s"" % (name, key)
##            printv(errormsg, 1, verbose)
##            raise
#
#    return par
#
#
#def makepars(data=None, framework=None, verbose=2, die=True, fixprops=None):
#    """
#    Translates the raw data (which were read from the spreadsheet) into
#    parameters that can be used in the model. These data are then used to update 
#    the corresponding model (project). 
#    
#    Version: 2018mar23
#    """
#    
#    printv("Converting data to parameters...", 1, verbose)
#    
#    ###############################################################################
#    ## Loop over quantities
#    ###############################################################################
#    
#    pars = odict()
#    
#    # Set up population keys
#    pars["popkeys"] = data["pop"].keys() # Get population keys
#    totkey = ["tot"] # Define a key for when not separated by population
#    popkeys = pars["popkeys"] # Convert to a normal string and to lower case...maybe not necessary
#    
#    # Read in parameters automatically
#    try: 
#        rawpars = framework.specs["par"] # Read the parameters structure
#    except AtomicaException as E: 
#        errormsg = "Could not load parameter specs: "%s"" % repr(E)
#        raise AtomicaException(errormsg)
#        
#    for parname,par in rawpars.iteritems(): # Iterate over all automatically read in parameters
#        printv("Converting data parameter "%s"..." % parname, 3, verbose)
#        
#        try: # Optionally keep going if some parameters fail
#        
##            # Shorten key variables
##            by = par["by"]
##            fromdata = par["fromdata"]
##            
##            # Decide what the keys are
##            if   by=="tot" : keys = totkey
##            elif by=="pop" : keys = popkeys
##            else: keys = [] 
##            
##            if fromdata: pars[parname] = data2timepar(parname=parname, data=data["par"][parname], keys=keys, **par) 
##            else: pars[parname] = Timepar(m=1.0, y=odict([(key,array([nan])) for key in keys]), t=odict([(key,array([0.0])) for key in keys]), **par) # Create structure
#
#            # TEMPORARY!!! - all parameters are assumed to be Timepars made from data and by population
#            keys = popkeys
#            pars[parname] = data2timepar(parname=parname, data=data["par"][parname], keys=keys, **par) 
#            
#        except Exception as E:
#            import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
#            errormsg = "Failed to convert parameter %s:\n%s" % (parname, repr(E))
#            if die: raise AtomicaException(errormsg)
#            else: printv(errormsg, 1, verbose)
#        
#    return pars
#
#
#def makesimpars(pars, name=None, keys=None, start=None, end=None, dt=None, tvec=None, settings=None, smoothness=None, asarray=True, sample=None, tosample=None, randseed=None, verbose=2):
#    """ 
#    A function for taking a single set of parameters and returning the interpolated versions.
#    Version: 2018mar26
#    """
#    
#    # Handle inputs and initialization
#    simpars = odict() 
#    simpars["parsetname"] = name
#    if keys is None: keys = pars.keys() # Just get all keys
#    if type(keys)==str: keys = [keys] # Listify if string
#    if tvec is not None: simpars["tvec"] = tvec
#    elif settings is not None: simpars["tvec"] = settings.maketvec(start=start, end=end, dt=dt)
#    else: simpars["tvec"] = inclusiverange(start=start, stop=end, step=dt) # Store time vector with the model parameters
#    if len(simpars["tvec"])>1: dt = simpars["tvec"][1] - simpars["tvec"][0] # Recalculate dt since must match tvec
#    simpars["dt"] = dt  # Store dt
#    if smoothness is None: smoothness = int(defaultsmoothness/dt)
#    tosample = promotetolist(tosample) # Convert to list
#    
#    # Copy default keys by default
##    for key in generalkeys: simpars[key] = dcp(pars[key])
##    for key in staticmatrixkeys: simpars[key] = dcp(array(pars[key]))
#
#    # Loop over requested keys
#    for key in keys: # Loop over all keys
#        if isinstance(pars[key], Par): # Check that it is actually a parameter
#            simpars[key] = dcp(pars[key])
#            thissample = sample # Make a copy of it to check it against the list of things we are sampling
#            if tosample[0] is not None and key not in tosample: thissample = False # Don"t sample from unselected parameters -- tosample[0] since it"s been promoted to a list
#            try:
#                simpars[key] = pars[key].interp(tvec=simpars["tvec"], dt=dt, smoothness=smoothness, asarray=asarray, sample=thissample, randseed=randseed)
#            except AtomicaException as E: 
#                errormsg = "Could not figure out how to interpolate parameter "%s"" % key
#                errormsg += "Error: "%s"" % repr(E)
#                raise AtomicaException(errormsg)
#
#
#    return simpars
#
#
#
#
#def applylimits(y, par=None, limits=None, dt=None, warn=True, verbose=2):
#    """ 
#    A function to  apply limits (supplied as [low, high] list or tuple) to an output.
#    Needs dt as input since that determines maxrate.
#    Version: 2018mar23
#    """
#    
#    # If parameter object is supplied, use it directly
#    parname = ""
#    if par is not None:
#        if limits is None: limits = par.limits
#        parname = par.name
#        
#    # If no limits supplied, don"t do anything
#    if limits is None:
#        printv("No limits supplied for parameter "%s"" % parname, 4, verbose)
#        return y
#    
#    if dt is None:
#        if warn: raise AtomicaException("No timestep specified: required for convertlimits()")
#        else: dt = 0.2 # WARNING, should probably not hard code this, although with the warning, and being conservative, probably OK
#    
#    # Convert any text in limits to a numerical value
#    limits = convertlimits(limits=limits, dt=dt, verbose=verbose)
#    
#    # Apply limits, preserving original class -- WARNING, need to handle nans
#    if isnumber(y):
#        if ~isfinite(y): return y # Give up
#        newy = median([limits[0], y, limits[1]])
#        if warn and newy!=y: printv("Note, parameter value "%s" reset from %f to %f" % (parname, y, newy), 3, verbose)
#    elif shape(y):
#        newy = array(y) # Make sure it"s an array and not a list
#        infiniteinds = findinds(~isfinite(newy))
#        infinitevals = newy[infiniteinds] # Store these for safe keeping
#        if len(infiniteinds): newy[infiniteinds] = limits[0] # Temporarily reset -- value shouldn"t matter
#        newy[newy<limits[0]] = limits[0]
#        newy[newy>limits[1]] = limits[1]
#        newy[infiniteinds] = infinitevals # And stick them back in
#        if warn and any(newy!=array(y)):
#            printv("Note, parameter "%s" value reset from:\n%s\nto:\n%s" % (parname, y, newy), 3, verbose)
#    else:
#        if warn: raise AtomicaException("Data type "%s" not understood for applying limits for parameter "%s"" % (type(y), parname))
#        else: newy = array(y)
#    
#    if shape(newy)!=shape(y):
#        errormsg = "Something went wrong with applying limits for parameter "%s":\ninput and output do not have the same shape:\n%s vs. %s" % (parname, shape(y), shape(newy))
#        raise AtomicaException(errormsg)
#    
#    return newy
