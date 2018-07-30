<!--
Manage projects page

Last update: 2018-07-29
-->

<template>
  <div class="SitePage">
    <div class="PageSection">

      <div class="ControlsRow">
        <button class="btn __blue" @click="addDemoProject">Create demo project</button>
        &nbsp; &nbsp;
        <button class="btn __blue" @click="createNewProjectModal">Create new project</button>
        &nbsp; &nbsp;
        <button class="btn __blue" @click="uploadProjectFromFile">Upload project from file</button>
        &nbsp; &nbsp;
      </div>
    </div>

    <div class="PageSection"
         v-if="projectSummaries.length > 0">
      <!--<h2>Manage projects</h2>-->

      <input type="text"
             class="txbox"
             style="margin-bottom: 20px"
             :placeholder="filterPlaceholder"
             v-model="filterText"/>

      <table class="table table-bordered table-hover table-striped" style="width: 100%">
        <thead>
          <tr>
            <th>
              <input type="checkbox" @click="selectAll()" v-model="allSelected"/>
            </th>
            <th @click="updateSorting('name')" class="sortable">
              Name
              <span v-show="sortColumn == 'name' && !sortReverse">
                <i class="fas fa-caret-down"></i>
              </span>
              <span v-show="sortColumn == 'name' && sortReverse">
                <i class="fas fa-caret-up"></i>
              </span>
              <span v-show="sortColumn != 'name'">
                <i class="fas fa-caret-up" style="visibility: hidden"></i>
              </span>
            </th>
            <th>Project actions</th>
            <th @click="updateSorting('creationTime')" class="sortable">
              Created on
              <span v-show="sortColumn == 'creationTime' && !sortReverse">
                <i class="fas fa-caret-down"></i>
              </span>
              <span v-show="sortColumn == 'creationTime' && sortReverse">
                <i class="fas fa-caret-up"></i>
              </span>
              <span v-show="sortColumn != 'creationTime'">
                <i class="fas fa-caret-up" style="visibility: hidden"></i>
              </span>
            </th>
            <th @click="updateSorting('updatedTime')" class="sortable">
              Last modified
              <span v-show="sortColumn == 'updatedTime' && !sortReverse">
                <i class="fas fa-caret-down"></i>
              </span>
              <span v-show="sortColumn == 'updatedTime' && sortReverse">
                <i class="fas fa-caret-up"></i>
              </span>
              <span v-show="sortColumn != 'updatedTime'">
                <i class="fas fa-caret-up" style="visibility: hidden"></i>
              </span>
            </th>
            <th>Populations</th>
            <th>Databook</th>
            <th>Program book</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="projectSummary in sortedFilteredProjectSummaries"
              :class="{ highlighted: projectIsActive(projectSummary.project.id) }">
            <td>
              <input type="checkbox" @click="uncheckSelectAll()" v-model="projectSummary.selected"/>
            </td>
            <td v-if="projectSummary.renaming !== ''">
              <input type="text"
                     class="txbox"
                     @keyup.enter="renameProject(projectSummary)"
                     v-model="projectSummary.renaming"/>
            </td>
            <td v-else>
              {{ projectSummary.project.name }}
            </td>
            <td>
              <button class="btn __green" @click="openProject(projectSummary.project.id)">Open</button>
              <button class="btn" @click="copyProject(projectSummary.project.id)" title="Copy">
                <i class="ti-files"></i>
              </button>
              <button class="btn" @click="renameProject(projectSummary)" title="Rename">
                <i class="ti-pencil"></i>
              </button>
              <button class="btn" @click="downloadProjectFile(projectSummary.project.id)" title="Download">
                <i class="ti-download"></i>
              </button>
            </td>
            <td>{{ projectSummary.project.creationTime.toUTCString() }}</td>
            <td>{{ projectSummary.project.updatedTime ? projectSummary.project.updatedTime.toUTCString():
              'No modification' }}</td>
            <td>
              {{ projectSummary.project.n_pops }}
            </td>
            <td>
              <button class="btn __blue" @click="uploadDatabook(projectSummary.project.id)" title="Upload">
                <i class="ti-upload"></i>
              </button>
              <button class="btn" @click="downloadDatabook(projectSummary.project.id)" title="Download">
                <i class="ti-download"></i>
              </button>
            </td>
            <td style="white-space: nowrap">
              <button class="btn __blue" @click="uploadProgbook(projectSummary.project.id)" title="Upload">
                <i class="ti-upload"></i>
              </button>
              <button class="btn" @click="downloadProgbook(projectSummary.project.id)" title="Download">
                <i class="ti-download"></i>
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="ControlsRow">
        <button class="btn" @click="deleteModal()">Delete selected</button>
        &nbsp; &nbsp;
        <button class="btn" @click="downloadSelectedProjects">Download selected</button>
      </div>
    </div>

    <modal name="create-project"
           height="auto"
           :classes="['v--modal', 'vue-dialog']"
           :width="width"
           :pivot-y="0.3"
           :adaptive="true"
           :clickToClose="clickToClose"
           :transition="transition">

      <div class="dialog-content">
        <div class="dialog-c-title">
          Create blank project
        </div>
        <div class="dialog-c-text">
          Project name:<br>
          <input type="text"
                 class="txbox"
                 v-model="proj_name"/><br>
          Number of populations:<br>
          <input type="text"
                 class="txbox"
                 v-model="num_pops"/><br>
          First year for data entry:<br>
          <input type="text"
                 class="txbox"
                 v-model="data_start"/><br>
          Final year for data entry:<br>
          <input type="text"
                 class="txbox"
                 v-model="data_end"/><br>
        </div>
        <div style="text-align:justify">
          <button @click="createNewProject()" class='btn __green' style="display:inline-block">
            Create
          </button>

          <button @click="$modal.hide('create-project')" class='btn __red' style="display:inline-block">
            Cancel
          </button>
        </div>
      </div>


      <div>

      </div>
    </modal>
    
    <!-- Popup spinner -->
    <popup-spinner></popup-spinner>
    
  </div>

</template>

<script>
import axios from 'axios'
var filesaver = require('file-saver')
import rpcservice from '@/services/rpc-service'
import progressIndicator from '@/services/progress-indicator-service'
import router from '@/router'
import PopupSpinner from './Spinner.vue'
  
export default {
  name: 'ProjectsPage',
  
  components: {
    PopupSpinner
  },
    
  data() {
    return {
      filterPlaceholder: 'Type here to filter projects', // Placeholder text for table filter box
      filterText: '',  // Text in the table filter box
      allSelected: false, // Are all of the projects selected?
      sortColumn: 'name',  // Column of table used for sorting the projects: name, country, creationTime, updatedTime, dataUploadTime
      sortReverse: false, // Sort in reverse order?
      projectSummaries: [], // List of summary objects for projects the user has
      proj_name: 'New project', // For creating a new project: number of populations
      num_pops: 5, // For creating a new project: number of populations
      data_start: 2000, // For creating a new project: number of populations
      data_end: 2035, // For creating a new project: number of populations
    }
  },

  computed: {
    sortedFilteredProjectSummaries() {
      return this.applyNameFilter(this.applySorting(this.projectSummaries))
//      return this.applyNameFilter(this.applySorting(this.applyCountryFilter(this.projectSummaries)))
    }
  },

  created() {
    let projectId = null
    
    // If we have no user logged in, automatically redirect to the login page.
    if (this.$store.state.currentUser.displayname == undefined) {
      router.push('/login')
    }

    // Otherwise...
    else {
      // Get the active project ID if there is an active project.
      if (this.$store.state.activeProject.project != undefined) {
        projectId = this.$store.state.activeProject.project.id
      }
      
      // Load the project summaries of the current user.
      this.updateProjectSummaries(projectId)
    }
  },

  methods: {

    beforeOpen (event) {
      console.log(event)
      // Set the opening time of the modal
      this.TEMPtime = Date.now()
    },

    beforeClose (event) {
      console.log(event)
      // If modal was open less then 5000 ms - prevent closing it
      if (this.TEMPtime + this.TEMPduration < Date.now()) {
        event.stop()
      }
    },

    updateProjectSummaries(setActiveID) {
      console.log('updateProjectSummaries() called')

      // Get the current user's project summaries from the server.
      rpcservice.rpcCall('load_current_user_project_summaries')
      .then(response => {
        let lastCreationTime = null
        let lastCreatedID = null
        
        // Set the projects to what we received.
        this.projectSummaries = response.data.projects
        
        // Initialize the last creation time stuff if we have a non-empty list.
        if (this.projectSummaries.length > 0) {
          lastCreationTime = new Date(this.projectSummaries[0].project.creationTime)
          lastCreatedID = this.projectSummaries[0].project.id
        }
        
        // Preprocess all projects.
        this.projectSummaries.forEach(theProj => {
          // Set to not selected.
          theProj.selected = false
            
          // Set to not being renamed.
          theProj.renaming = ''
            
          // Extract actual Date objects from the strings.
          theProj.project.creationTime = new Date(theProj.project.creationTime)
          theProj.project.updatedTime = new Date(theProj.project.updatedTime)
          
          // Update the last creation time and ID if what se see is later.
          if (theProj.project.creationTime >= lastCreationTime) {
            lastCreationTime = theProj.project.creationTime
            lastCreatedID = theProj.project.id
          } 
        }) 
          
        // If we have a project on the list...
        if (this.projectSummaries.length > 0) {
          // If no ID is passed in, set the active project to the last-created 
          // project.
          if (setActiveID == null) {
            this.openProject(lastCreatedID)            
          }
          
          // Otherwise, set the active project to the one passed in.
          else {
            this.openProject(setActiveID)
          }
        }
      })
      .catch(error => {
        // Failure popup.
        progressIndicator.failurePopup(this, 'Could not load projects')    
      })     
    },

    addDemoProject() {
      console.log('addDemoProject() called')
      
      // Start indicating progress.
      progressIndicator.start(this)
      
      // Have the server create a new project.
      rpcservice.rpcCall('add_demo_project', [this.$store.state.currentUser.UID])
      .then(response => {
        // Update the project summaries so the new project shows up on the list.
        this.updateProjectSummaries(response.data.projectId)
        
        // Indicate success.
        progressIndicator.succeed(this, 'Demo project added')
      })
      .catch(error => {
        // Indicate failure.
        progressIndicator.fail(this, 'Could not add project') 
      })
    },

    createNewProjectModal() {
      // Open a model dialog for creating a new project
      console.log('createNewProjectModal() called');
      this.$modal.show('create-project');
    },


    createNewProject() {
      console.log('createNewProject() called')
      this.$modal.hide('create-project')
      
      // Start indicating progress.
      progressIndicator.start(this)
      
      // Have the server create a new project.
      rpcservice.rpcDownloadCall('create_new_project', [this.$store.state.currentUser.UID, this.proj_name, this.num_pops, this.data_start, this.data_end])
      .then(response => {
        // Update the project summaries so the new project shows up on the list.
        // Note: There's no easy way to get the new project UID to tell the 
        // project update to choose the new project because the RPC cannot pass 
        // it back.
        this.updateProjectSummaries(null)
        
        // Indicate success.
        progressIndicator.succeed(this, 'New project "' + this.proj_name + '" created')
      })
      .catch(error => {
        // Indicate failure.
        progressIndicator.fail(this, 'Could not add new project')   
      })  
    },

    uploadProjectFromFile() {
      console.log('uploadProjectFromFile() called')
     
      // Have the server upload the project.
      rpcservice.rpcUploadCall('create_project_from_prj_file', [this.$store.state.currentUser.UID], {}, '.prj')
      .then(response => {
        // Start indicating progress. (This is here because we don't want the 
        // progress bar and spinner running when the user is picking a file to upload.)
        progressIndicator.start(this)
      
        // Update the project summaries so the new project shows up on the list.
        this.updateProjectSummaries(response.data.projectId)
        
        // Indicate success.
        progressIndicator.succeed(this, 'New project uploaded')       
      })
      .catch(error => {
        // Indicate failure.
        progressIndicator.fail(this, 'Could not upload file')     
      }) 
    },

    projectIsActive(uid) {
      // If the project is undefined, it is not active.
      if (this.$store.state.activeProject.project === undefined) {
        return false
      }

      // Otherwise, the project is active if the UIDs match.
      else {
        return (this.$store.state.activeProject.project.id === uid)
      }
    },

    selectAll() {
      console.log('selectAll() called')

      // For each of the projects, set the selection of the project to the
      // _opposite_ of the state of the all-select checkbox's state.
      // NOTE: This function depends on it getting called before the
      // v-model state is updated.  If there are some cases of Vue
      // implementation where these happen in the opposite order, then
      // this will not give the desired result.
      this.projectSummaries.forEach(theProject => theProject.selected = !this.allSelected)
    },

    uncheckSelectAll() {
      this.allSelected = false
    },

    updateSorting(sortColumn) {
      console.log('updateSorting() called')

      // If the active sorting column is clicked...
      if (this.sortColumn === sortColumn) {
          // Reverse the sort.
          this.sortReverse = !this.sortReverse
      }
      // Otherwise.
      else {
        // Select the new column for sorting.
        this.sortColumn = sortColumn

        // Set the sorting for non-reverse.
        this.sortReverse = false
      }
    },

    applyNameFilter(projects) {
      return projects.filter(theProject => theProject.project.name.toLowerCase().indexOf(this.filterText.toLowerCase()) !== -1)
    },

    applySorting(projects) {
      return projects.slice(0).sort((proj1, proj2) =>
        {
          let sortDir = this.sortReverse ? -1: 1
          if (this.sortColumn === 'name') {
            return (proj1.project.name.toLowerCase() > proj2.project.name.toLowerCase() ? sortDir: -sortDir)
          }
/*          else if (this.sortColumn === 'country') {
            return proj1.country > proj2.country ? sortDir: -sortDir
          } */
          else if (this.sortColumn === 'creationTime') {
            return proj1.project.creationTime > proj2.project.creationTime ? sortDir: -sortDir
          }
          else if (this.sortColumn === 'updatedTime') {
            return proj1.project.updatedTime > proj2.project.updatedTime ? sortDir: -sortDir
          }
        }
      )
    },

/*    applyCountryFilter(projects) {
      if (this.selectedCountry === 'Select country...')
        return projects
      else
        return projects.filter(theProj => theProj.country === this.selectedCountry)
    }, */

    openProject(uid) {
      // Find the project that matches the UID passed in.
      let matchProject = this.projectSummaries.find(theProj => theProj.project.id === uid)

      console.log('openProject() called for ' + matchProject.project.name)
          

// Code for testing loading bar.  
/*      this.$Progress.start()      // with this (default) setting, the bar takes about 7 sec. to fully progress        
//      this.$Progress.start(9700)  // with this setting, about 75% of the bar is progressed in 5 min.
      this.$Progress.setTransition(
        {
          speed: '0.2s',
          opacity: '0.6s',
          termination: 1000  // milliseconds that bar stays around after finish or fail
        })
        
//      rpcservice.rpcCall('simulate_slow_rpc', [7, true])  // 7 seconds, then succeed  
      rpcservice.rpcCall('simulate_slow_rpc', [7, false])  // 7 seconds, then fail
      .then(response => { 
        this.$Progress.finish()         
      })
      .catch(error => {
        this.$Progress.fail()
      }) */
      
      
      // Set the active project to the matched project.
      this.$store.commit('newActiveProject', matchProject)
      
      // Success popup.
      progressIndicator.successPopup(this, 'Project "'+matchProject.project.name+'" loaded')
    },

    copyProject(uid) {
      // Find the project that matches the UID passed in.
      let matchProject = this.projectSummaries.find(theProj => theProj.project.id === uid)

      console.log('copyProject() called for ' + matchProject.project.name)
      
      // Start indicating progress.
      progressIndicator.start(this)
      
      // Have the server copy the project, giving it a new name.
      rpcservice.rpcCall('copy_project', [uid])
      .then(response => {
        // Update the project summaries so the copied program shows up on the list.
        this.updateProjectSummaries(response.data.projectId)
        
        // Indicate success.
        progressIndicator.succeed(this, 'Project "'+matchProject.project.name+'" copied')       
      })
      .catch(error => {
        // Indicate failure.
        progressIndicator.fail(this, 'Could not copy project')
      })
    },

    renameProject(projectSummary) {
      console.log('renameProject() called for ' + projectSummary.project.name)

      // If the project is not in a mode to be renamed, make it so.
      if (projectSummary.renaming === '') {
        projectSummary.renaming = projectSummary.project.name
      }

      // Otherwise (it is to be renamed)...
      else {
        // Make a deep copy of the projectSummary object by JSON-stringifying the old
        // object, and then parsing the result back into a new object.
        let newProjectSummary = JSON.parse(JSON.stringify(projectSummary))

        // Rename the project name in the client list from what's in the textbox.
        newProjectSummary.project.name = projectSummary.renaming
        
        // Start indicating progress.
        progressIndicator.start(this)
        
        // Have the server change the name of the project by passing in the new copy of the
        // summary.
        rpcservice.rpcCall('update_project_from_summary', [newProjectSummary])
        .then(response => {
          // Update the project summaries so the rename shows up on the list.
          this.updateProjectSummaries(newProjectSummary.project.id)

          // Turn off the renaming mode.
          projectSummary.renaming = ''
          
          // Indicate success.
          progressIndicator.succeed(this, '')  // No green popup message.          
        })
        .catch(error => {
          // Indicate failure.
          progressIndicator.fail(this, 'Could not rename project')    
        })      
      }

      // This silly hack is done to make sure that the Vue component gets updated by this function call.
      // Something about resetting the project name informs the Vue component it needs to
      // update, whereas the renaming attribute fails to update it.
      // We should find a better way to do this.
      let theName = projectSummary.project.name
      projectSummary.project.name = 'newname'
      projectSummary.project.name = theName
    },

    downloadProjectFile(uid) {
      // Find the project that matches the UID passed in.
      let matchProject = this.projectSummaries.find(theProj => theProj.project.id === uid)

      console.log('downloadProjectFile() called for ' + matchProject.project.name)
      
      // Start indicating progress.
      progressIndicator.start(this)
        
      // Make the server call to download the project to a .prj file.
      rpcservice.rpcDownloadCall('download_project', [uid])
      .then(response => {
        // Indicate success.
        progressIndicator.succeed(this, '')  // No green popup message.        
      })
      .catch(error => {
        // Indicate failure.
        progressIndicator.fail(this, 'Could not download project')      
      })
    },

    downloadDatabook(uid) {
      // Find the project that matches the UID passed in.
//      let matchProject = this.projectSummaries.find(theProj => theProj.project.id === uid)
//
//      console.log('downloadDatabook() called for ' + matchProject.project.name)
//
//      // Make the server call to download the project to a .prj file.
//      rpcservice.rpcDownloadCall('download_databook', [uid])
        this.$notifications.notify({
          message: 'This is not yet implemented, please check back soon.',
          icon: 'ti-face-sad',
          type: 'warning',
          verticalAlign: 'top',
          horizontalAlign: 'center',
        });

      },

    downloadProgbook(uid) {
      // Find the project that matches the UID passed in.
      let matchProject = this.projectSummaries.find(theProj => theProj.project.id === uid)

      console.log('downloadProgbook() called for ' + matchProject.project.name)
      
      // Start indicating progress.
      progressIndicator.start(this)
      
      // Make the server call to download the project to a .prj file.
      rpcservice.rpcDownloadCall('download_progbook', [uid])
      .then(response => {
        // Indicate success.
        progressIndicator.succeed(this, '')  // No green popup message.          
      })
      .catch(error => {
        // Indicate failure.
        progressIndicator.fail(this, 'Could not download progbook')     
      })      
    },

    downloadDefaults(uid) {
      // Find the project that matches the UID passed in.
      let matchProject = this.projectSummaries.find(theProj => theProj.project.id === uid)

      console.log('downloadDefaults() called for ' + matchProject.project.name)
      
      // Start indicating progress.
      progressIndicator.start(this)
      
      // Make the server call to download the project to a .prj file.
      rpcservice.rpcDownloadCall('download_defaults', [uid])
      .then(response => {
        // Indicate success.
        progressIndicator.succeed(this, '')  // No green popup message.        
      })
      .catch(error => {
        // Indicate failure.
        progressIndicator.fail(this, 'Could not download defaults')     
      })       
    },

    uploadDatabook(uid) {
      // Find the project that matches the UID passed in.
      let matchProject = this.projectSummaries.find(theProj => theProj.project.id === uid)

      console.log('uploadDatabook() called for ' + matchProject.project.name)

      // Have the server copy the project, giving it a new name.
      rpcservice.rpcUploadCall('upload_databook', [uid], {})
      .then(response => {
        // Start indicating progress. (This is here because we don't want the 
        // progress bar and spinner running when the user is picking a file to upload.)
        progressIndicator.start(this)
        
        // Update the project summaries so the copied program shows up on the list.
        this.updateProjectSummaries(uid)
        
        // Indicate success.
        progressIndicator.succeed(this, 'Data uploaded to project "'+matchProject.project.name+'"')     
      })
      .catch(error => {
        // Indicate failure.
        progressIndicator.fail(this, 'Could not upload data')     
      })
    },

    uploadProgbook(uid) {
      // Find the project that matches the UID passed in.
      let matchProject = this.projectSummaries.find(theProj => theProj.project.id === uid)

      console.log('uploadProgbook() called for ' + matchProject.project.name)

      // Have the server copy the project, giving it a new name.
      rpcservice.rpcUploadCall('upload_progbook', [uid], {})
      .then(response => {
        // Start indicating progress. (This is here because we don't want the 
        // progress bar and spinner running when the user is picking a file to upload.)
        progressIndicator.start(this)
          
        // Update the project summaries so the copied program shows up on the list.
        this.updateProjectSummaries(uid)
        
        // Indicate success.
        progressIndicator.succeed(this, 'Programs uploaded to project "'+matchProject.project.name+'"')        
      })
      .catch(error => {
        // Indicate failure.
        progressIndicator.fail(this, 'Could not upload progbook')     
      })
    },

    // Confirmation alert
    deleteModal() {
      // Pull out the names of the projects that are selected.
      let selectProjectsUIDs = this.projectSummaries.filter(theProj =>
        theProj.selected).map(theProj => theProj.project.id)
        
      // Only if something is selected...
      if (selectProjectsUIDs.length > 0) {         
        // Alert object data
        var obj = {
              message: 'Are you sure you want to delete the selected projects?',
              useConfirmBtn: true,
              customConfirmBtnClass: 'btn __red',
              customCloseBtnClass: 'btn',
              onConfirm: this.deleteSelectedProjects
            }
        this.$Simplert.open(obj)
      }
    },

    deleteSelectedProjects() {
      // Pull out the names of the projects that are selected.
      let selectProjectsUIDs = this.projectSummaries.filter(theProj =>
        theProj.selected).map(theProj => theProj.project.id)

      console.log('deleteSelectedProjects() called for ', selectProjectsUIDs)

      // Have the server delete the selected projects.
      if (selectProjectsUIDs.length > 0) {
        // Start indicating progress.
        progressIndicator.start(this)
      
        rpcservice.rpcCall('delete_projects', [selectProjectsUIDs])
        .then(response => {
          // Get the active project ID.
          let activeProjectId = this.$store.state.activeProject.project.id
          if (activeProjectId === undefined) {
            activeProjectId = null
          } 
          
          // If the active project ID is one of the ones deleted...
          if (selectProjectsUIDs.find(theId => theId === activeProjectId)) {
            // Set the active project to an empty project.
            this.$store.commit('newActiveProject', {})   

            // Null out the project.
            activeProjectId = null            
          }
          
          // Update the project summaries so the deletions show up on the list. 
          // Make sure it tries to set the project that was active (if any).
          this.updateProjectSummaries(activeProjectId)
          
          // Indicate success.
          progressIndicator.succeed(this, '')  // No green popup message.
        })
        .catch(error => {
          // Indicate failure.
          progressIndicator.fail(this, 'Could not delete project/s')     
        }) 
      }
    },

    downloadSelectedProjects() {
      // Pull out the names of the projects that are selected.
      let selectProjectsUIDs = this.projectSummaries.filter(theProj =>
        theProj.selected).map(theProj => theProj.project.id)

      console.log('downloadSelectedProjects() called for ', selectProjectsUIDs)
          
      // Have the server download the selected projects.
      if (selectProjectsUIDs.length > 0) {
        // Start indicating progress.
        progressIndicator.start(this)
        
        rpcservice.rpcDownloadCall('load_zip_of_prj_files', [selectProjectsUIDs])
        .then(response => {
          // Indicate success.
          progressIndicator.succeed(this, '')  // No green popup message.         
        })
        .catch(error => {
          // Indicate failure.
          progressIndicator.fail(this, 'Could not download project/s')     
        })       
      }
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang="scss" scoped>
</style>
