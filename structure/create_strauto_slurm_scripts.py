#!/usr/bin/env python
''' 
create_strauto_slurm_scripts.py
===============================

This script is designed to be a supplement to running Structure[1] jobs on
Compute Canada HPC clusters that are using the Slurm Workload manager.
It is meant to be used with Structure, StrAuto[2] and StructureHarvester[3].

Usage:
******

* Place this script 'create_strauto_slurm_scripts.py' into a directory along with
    * 'strauto_1.py' and 'input.py' from StrAuto[2].
    * 'structureHarvester.py' and 'harvesterCore.py' from StructureHarvester[3]
    * The file with the Structure dataset e.g. 'sim.str'.
* Edit the settings in 'input.py' as described in the StrAuto User Manual.
    * Make sure to set the option 'parallel = True' (question 23).
* Adjust the parameters in this file (ca. lines 65-70):
    * Set 'max_jobtime' to a duration where you can be reasonably sure that no
      individual Structure run takes longer than this.
    * In cases where a user can submit under multiple Slurm-accounts
      'slurm_account' can be used to specify under which account to submit.
    * To avoid overloading the Scheduler, the submission helper script delays
      each submission by a time defined by 'submit_delay'.
* Run the following commands:
    * ./strauto_1.py
    * ./create_strauto_slurm_scripts.py
* Submit the jobs with:
    * ./submit_strauto_jobs.sh
* After all jobs have completed, run './post_strauto.sh' to aggregate the
  results and run StructureHarvester.

[1] Structure: http://web.stanford.edu/group/pritchardlab/structure.html
[2] StrAuto:   http://www.crypticlineage.net/pages/software.html
[3] Harvester: http://alumni.soe.ucsc.edu/~dearl/software/structureHarvester/
               https://github.com/dentearl/structureHarvester

LICENSE:
========
This program is licensed under the conditions of the "MIT License".

Copyright 2017-2020 Oliver Stueker <ostueker(a)ace-net.ca>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.
'''
from __future__ import print_function
import re, os, sys
##############################################################################
### Please adjust the following parameters:
##############################################################################
max_jobtime = '1-0:00:0' # format: d-hh:mm:ss
slurm_account = None     # e.g.: slurm_account='def-somegroup'
submit_delay = '0.5s'    # pause this long between job submissions
job_prefix = None        # (optional) e.g.: job_prefix='strauto'

##############################################################################
### Don't make any changes below this line:
##############################################################################
template = '''#!/bin/bash
#SBATCH --ntasks=1
#SBATCH --time={MAXTIME:}              # d-hh:mm:ss
#SBATCH --job-name={JOBNAME:}
#SBATCH --chdir={DIRECTORY:}
#SBATCH --output=%x_%j_slurm.out
{SLURM_ACCT:}
module load structure/2.3.4

{STRUCTURE_COMMAND}
'''

post_template = '''#!/bin/bash
mv {KLIST:} results_f/
mkdir harvester_input
cp results_f/k*/*_f harvester_input
echo "The structure runs have finished."

# Run structureHarvester.py
./structureHarvester.py --dir harvester_input --out harvester --evanno --clumpp
echo 'structureHarvester run has finished.'

# Clean up Harvester input files.
zip {DATASET:}_Harvester_Upload.zip harvester_input/*
mv {DATASET:}_Harvester_Upload.zip harvester/
rm -rf harvester_input
'''

if __name__ == '__main__':
    if not os.path.exists('structureCommands'):
        print('ERROR: File "structureCommands" does not exist!')
        print('You need to run "./strauto_1.py" before running "{}".'
              .format(os.path.basename(sys.argv[0])))
        sys.exit(1)
    # initialize some variables
    scripts_dir = 'slurm_scripts'
    job_directory = os.getcwd()
    if slurm_account:
        slurm_account = '#SBATCH --account='+slurm_account
    else:
        slurm_account = ''
    re_jobname = re.compile(r'-o (k\d+)/((.+)_\1_run\d+) ')
    job_scripts = []
    klist = set()
    
    with open('structureCommands', 'r') as structureCommands:
        print("Creating SLURM job scripts...")
        for line in structureCommands:
            match = re_jobname.search(line)
            if match:
                kn = match.group(1)
                jobname = match.group(2)
                dataset = match.group(3)

                klist.add(kn)
                if job_prefix:
                    jobname = '_'.join([job_prefix, jobname])

                line = line.replace('./structure', 'structure')

                job_script_content = template.format(
                        SLURM_ACCT=slurm_account,
                        MAXTIME=max_jobtime,
                        JOBNAME=jobname,
                        DIRECTORY=job_directory,
                        STRUCTURE_COMMAND=line,
                    )

                if not ( os.path.exists(scripts_dir) and
                         os.path.isdir(scripts_dir) ):
                    os.mkdir(scripts_dir)

                job_script_name = os.path.join( scripts_dir,
                                    'slurm_job_{:}.sh'.format(jobname))
                with open(job_script_name, 'w') as slurm_script:
                    slurm_script.write(job_script_content)
                job_scripts.append(job_script_name)
        print("created {:} job scripts.\n".format(len(job_scripts)))

    print("Creating directories...", end='')
    directories = ['results_f', 'log', 'harvester']
    for kn in sorted(klist):
        directories.append(kn)
        directories.append(os.path.join('log', kn))
    print('done!', end='\n\n')

    for directory in directories:
        if not os.path.exists(directory):
            os.mkdir(directory)

    print('Creating submission helper script...')
    helper_script_name='submit_strauto_jobs.sh'
    with open(helper_script_name, 'w') as helper_script:
        helper_script.write('#!/bin/bash\n')
        for job_script in job_scripts:
            helper_script.write('sleep 0.5s ; sbatch {:}\n'.format(job_script))
    print('created helper script: "{:}"\n'.format(helper_script_name))

    print('Creating postprocessing script...')
    post_script_name='post_strauto.sh'
    with open(post_script_name, 'w') as pst_script:
        pst_script.write(post_template.format(KLIST=' '.join(sorted(klist)),
                                              DATASET=dataset))
    print('created post-script: "{:}"\n'.format(post_script_name))