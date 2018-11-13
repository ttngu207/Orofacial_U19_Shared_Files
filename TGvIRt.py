import sys
import os
sys.path.insert(0, os.path.join('..','wanglab-general'))
import datajoint as dj

dj.config['database.host'] = '10.122.171.76'
dj.config['database.user'] = 'vincent'        
dj.config['names.labschema'] = 'wanglab'     
dj.config['names.project'] = 'TGvIRt' 

import wanglab as lab

schema = dj.schema(dj.config['names.project'], locals())


@schema
class Surgery(dj.Manual):
    definition = """
    -> lab.Subject
    --- 
    surgery : varchar(4000)    # description of surgery
    """
    

@schema
class InjectionSite(dj.Manual):
    definition = """
    -> lab.Subject
    site : tinyint  # vector injection site
    ---
    injection_x : decimal(3,2)   # (mm)
    injection_y : decimal(3,2)   # (mm)
    injection_z : decimal(3,2)   # (mm)
    """

@schema
class TargetRegion(dj.Lookup):
    definition = """
    target_region : varchar(12)
    """
    contents = zip(['PrV', 'FN', 'VPM', 'PO', 'WhiskerPad', 'SpVi', 'SpVir', 'S1', 'M1', 'Cerebellum', 'SC', 'vIRt', 'brainstem', 'other', 'sham'])


@schema
class Session(dj.Manual):
    definition = """
    -> lab.Subject
    session  : int   # session within 
    --- 
    -> lab.Study
    session_date       : date         # session date 
    session_suffix='': char(2)         # suffix used by experimenter when identifying session by date
    session_notes='' : varchar(4000)   # free-text notes
    session_folder='': varchar(255)    # path to session data for data import
    recording_type  : varchar(20)   # e.g. acute   
    """

@schema
class CueType(dj.Lookup):
    definition = """
    cue_type : varchar(20)  
    """
    contents = zip(['cuetip','whiskerstim','piezo_deflection',
        'touch_panel','pole','start', 'response'])

@schema
class WhiskerBehavior(dj.Imported):
    definition = """
    -> Session
    """

    class Angles(dj.Part):
        definition = """
        -> WhiskerBehavior
        ---
        angle         : longblob   # (degrees) deviation
        curve         : longblob   # (radians/mm)   
        frame_times   : longblob   # (s)
        """
    
    class WhiskerTouch(dj.Part):
        definition = """
        -> WhiskerBehavior
        ---
        retract_times   : longblob  # (s)    
        protract_times  : longblob  # (s)
        """

@schema
class OptoStim(dj.Manual):
    definition = """
    # Optogenetic stimulation information for the sesssion
    -> Session
    """
    
    class Site(dj.Part):
        definition = """
        # Optogenetic stimulation site
        -> OptoStim
        -> TargetRegion
        site_number   : tinyint  #  optogenetic site number  
        ---
        description : varchar(255)   # optogenetic site description
        """
    class StimParam(dj.Part):
        definition = """
        # Optogenetic stimulation parameters
        -> OptoStim.Site
        stim_number   : tinyint  #  optogenetic stim sequence number  
        ---
        stimulation_method  : varchar(255)
        device   : varchar(60)
        location_x  : decimal(4,2)  # mm
        location_y  : decimal(4,2)  # mm
        laser_wavelength : decimal(4,1)  # nm 
        laser_power : decimal(4,1)  # mW
        pulse_duration : smallint # ms
        pulse_frequency : smallint # Hz
        pulse_per_train : smallint #
        """

@schema
class Ephys(dj.Manual):
    definition = """
    -> Session
    -> lab.Rig
    ---
    recording_marker: varchar(30)  # e.g. "stereotaxic" or "implant"
    # ground_x  : decimal(4,2)   # (mm) #no need for those
    # ground_y  : decimal(4,2)   # (mm)
    # ground_z  : decimal(4,2)   # (mm)
    recording_notes='' : varchar(4000)   # free-text notes 
    """
    
    class Shank(dj.Part):
        definition = """
        -> Ephys
        shank  : tinyint  # shank of probe
        ---
        -> TargetRegion
        # posterior :  decimal(3,2)   # (mm) #useless
        # lateral  :  decimal(3,2)   # (mm) #useless
        """
    
    class Electrode(dj.Part):
        definition = """
        -> Ephys
        electrode : tinyint   # electrode on probe
        ---
        -> Ephys.Shank
        electrode_x  : decimal(6,4)  # (mm) electrode map
        electrode_y  : decimal(6,4)  # (mm) electrode map
        electrode_z  : decimal(6,4)  # (mm) electrode map
        """    

@schema
class Phototag(dj.Manual):
    definition = """
    -> Ephys
    -> OptoStim
    ---
    responses  : varchar(30)   # Yes / No / MU / SU
    responsive_channels= null : varchar(30)  # responsive channels
    """

@schema
class CellType(dj.Lookup):
    definition = """
    cell_type  : varchar(12)
    """
    contents = zip(['pyramidal', 'FS'])


@schema
class SpikeSortingMethod(dj.Lookup):
    definition = """
    spike_sort_method           : varchar(12)           # spike sort short name
    ---
    spike_sort_description      : varchar(1024)
    """
    #contents = [('default', 'spyking_circus')] # waveform shape ChR tagging and collision test


@schema
class SpikeSorting(dj.Imported):
    definition = """
    -> Ephys
    -> SpikeSortingMethod
    """
    
    class Unit(dj.Part):
        definition = """
        -> SpikeSorting
        unit  : smallint   # single unit number in recording
        """
        
    class CellType(dj.Part):
        definition = """
        -> SpikeSorting.Unit
        ---
        -> CellType
        """
        
    class Spikes(dj.Part):
        definition = """
        -> SpikeSorting.Unit
        ---
        spike_times : longblob  
        """
        
    class Waveform(dj.Part):
        definition = """
        -> SpikeSorting.Unit
        -> Ephys.Electrode
        ---
        waveform : longblob   # uV 
        """


@schema
class Trial(dj.Imported):
    definition = """
    # Trial within a session
    -> Session
    trial   : smallint   # trial number within session
    ---
    start_time : float   # (s) synchronized
    stop_time  : float   # (s) synchronized
    """
    class TrialType(dj.Part):
        definition = """
        -> Trial
        ---
        trial_type  : varchar(12)
        """
        
    class Cue(dj.Part):
        definition = """
        -> Trial
        -> CueType 
        ---
        cue_time  : double                      # synchronized
        """
 
    class Stim(dj.Part):
        definition = """
        -> Trial
        -> OptoStim 
        ---
        stim_time  : double                      # synchronized
        """
        
    class UnitInTrial(dj.Part):
        definition = """
        -> Trial 
        -> SpikeSorting.Unit
        """