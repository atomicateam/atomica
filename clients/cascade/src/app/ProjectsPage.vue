<!--
Manage projects page

Last update: 2018-08-23
-->

<template>
  <div>
    <div class="PageSection">
      <help-link :ref="create-projects" :label="'Create projects'"></help-link>
      
      <div class="ControlsRow">
        <button class="btn __blue" @click="addDemoProjectModal">Create demo project</button>
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
            <th style="text-align:center">Framework</th>
            <!--<th style="text-align:center">Populations</th>-->
            <th style="text-align:center">Databook</th>
            <th style="text-align:center">Program book</th>
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
              <button class="btn __green" :disabled="projectLoaded(projectSummary.project.id)" @click="openProject(projectSummary.project.id)">
                <span v-if="projectLoaded(projectSummary.project.id)">Selected</span>
                <span v-else>Open</span>
              </button>
              <button class="btn" @click="renameProject(projectSummary)" data-tooltip="Rename">
                <i class="ti-pencil"></i>
              </button>
              <button class="btn" @click="copyProject(projectSummary.project.id)" data-tooltip="Copy">
                <i class="ti-files"></i>
              </button>
              <button class="btn" @click="downloadProjectFile(projectSummary.project.id)" data-tooltip="Download">
                <i class="ti-download"></i>
              </button>
            </td>
            <td>{{ projectSummary.project.creationTime.toUTCString() }}</td>
            <td>{{ projectSummary.project.updatedTime ? projectSummary.project.updatedTime.toUTCString():
              'No modification' }}</td>
            <td style="text-align:right">
              {{ projectSummary.project.framework }}
              <button class="btn" @click="downloadFramework(projectSummary.project.id)" data-tooltip="Download">
                <i class="ti-download"></i>
              </button>
            </td>
            <!--<td style="text-align:center">-->
              <!--{{ projectSummary.project.n_pops }}-->
            <!--</td>-->
            <td style="text-align:center">
              <button class="btn __blue" @click="uploadDatabook(projectSummary.project.id)" data-tooltip="Upload">
                <i class="ti-upload"></i>
              </button>
              <button class="btn" @click="downloadDatabook(projectSummary.project.id)" data-tooltip="Download">
                <i class="ti-download"></i>
              </button>
            </td>
            <td style="white-space: nowrap; text-align:center">
              <button class="btn __green" @click="createProgbookModal(projectSummary.project.id)" data-tooltip="New">
                <i class="ti-plus"></i>
              </button>
              <button class="btn __blue" @click="uploadProgbook(projectSummary.project.id)" data-tooltip="Upload">
                <i class="ti-upload"></i>
              </button>
              <button class="btn" @click="downloadProgbook(projectSummary.project.id)" data-tooltip="Download">
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

    <modal name="demo-project"
           height="auto"
           :classes="['v--modal', 'vue-dialog']"
           :width="width"
           :pivot-y="0.3"
           :adaptive="true"
           :clickToClose="clickToClose"
           :transition="transition">

      <div class="dialog-content">
        <div class="dialog-c-title">
          Create demo project
        </div>
        <div class="dialog-c-text">
          <select v-model="demoOption">
            <option v-for='project in demoOptions'>
              {{ project }}
            </option>
          </select><br><br>
        </div>
        <div style="text-align:justify">
          <button @click="addDemoProject()" class='btn __green' style="display:inline-block">
            Add selected
          </button>

          <button @click="$modal.hide('demo-project')" class='btn __red' style="display:inline-block">
            Cancel
          </button>
        </div>
      </div>
    </modal>

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
          Create new project
        </div>
        
        <div v-if="frameworkSummaries.length>0">     
          <div class="dialog-c-text">
            Project name:<br>
            <input type="text"
                   class="txbox"
                   v-model="proj_name"/><br>
            Framework:<br>
            <select v-model="currentFramework">
              <option v-for='frameworkSummary in frameworkSummaries'>
                {{ frameworkSummary.framework.name }}
              </option>
            </select><br><br>
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
        
        <div v-else>
          <div class="dialog-c-text">        
            Before creating a new project, please create or upload at least one framework.
          </div>
          <br>
          <div style="text-align:justify">
            <button @click="$modal.hide('create-project')" class='btn' style="display:inline-block">
              Ok
            </button>
          </div>          
        </div>
        
      </div>
    </modal>

    <modal name="create-progbook"
           height="auto"
           :classes="['v--modal', 'vue-dialog']"
           :width="width"
           :pivot-y="0.3"
           :adaptive="true"
           :clickToClose="clickToClose"
           :transition="transition">

      <div class="dialog-content">
        <div class="dialog-c-title">
          Create program book
        </div>
        <div class="dialog-c-text">
          Number of programs:<br>
          <input type="text"
                 class="txbox"
                 v-model="num_progs"/><br>
        </div>
        <div style="text-align:justify">
          <button @click="createProgbook()" class='btn __green' style="display:inline-block">
            Create
          </button>

          <button @click="$modal.hide('create-progbook')" class='btn __red' style="display:inline-block">
            Cancel
          </button>
        </div>
      </div>
    </modal>
    
  </div>

</template>

<script>
import axios from 'axios'
var filesaver = require('file-saver')
import utils from '@/services/utils'
import rpcs from '@/services/rpc-service'
import status from '@/services/status-service'
import router from '@/router'
import HelpLink from '@/app/HelpLink.vue'
  
export default {
  name: 'ProjectsPage',
 
  components: {
    HelpLink
  }, 
  
  data() {
    return {
      filterPlaceholder: 'Type here to filter projects', // Placeholder text for table filter box
      filterText: '',  // Text in the table filter box
      allSelected: false, // Are all of the projects selected?
      sortColumn: 'name',  // Column of table used for sorting the projects: name, country, creationTime, updatedTime, dataUploadTime
      sortReverse: false, // Sort in reverse order?
      projectSummaries: [], // List of summary objects for projects the user has
      proj_name:  'New project', // For creating a new project: number of populations
      num_pops:   5, // For creating a new project: number of populations
      num_progs:  5, // For creating a new project: number of populations
      data_start: 2000, // For creating a new project: number of populations
      data_end:   2035, // For creating a new project: number of populations
      activeuid:  [], // WARNING, kludgy to get create progbook working
      frameworkSummaries: [],
      currentFramework: '',
      demoOptions: [],
      demoOption: '',
    }
  },

  computed: {
    sortedFilteredProjectSummaries() {
      return this.applyNameFilter(this.applySorting(this.projectSummaries))
    },
  },

  created() {
    let projectId = null
    if (this.$store.state.currentUser.displayname == undefined) { // If we have no user logged in, automatically redirect to the login page.
      router.push('/login')
    } else {    // Otherwise...
      if (this.$store.state.activeProject.project != undefined) { // Get the active project ID if there is an active project.
        projectId = this.$store.state.activeProject.project.id
      }
      this.getDemoOptions()
      this.updateFrameworkSummaries()        // Load the frameworks so the new project dialog is populated
      this.updateProjectSummaries(projectId) // Load the project summaries of the current user.
    }
  },

  methods: {
    
/*    openThang(thangLink) {
      let scrh = screen.height
      let scrw = screen.width
      let h = scrh * 0.8  // Height of window
      let w = scrw * 0.6  // Width of window
      let t = scrh * 0.1  // Position from top of screen -- centered
      let l = scrw * 0.37 // Position from left of screen -- almost all the way right      
      let newWindow = window.open(thangLink, 
        'Reference manual', 'width=' + w + ', height=' + h + ', top=' + t + ',left=' + l)
      if (window.focus) {
        newWindow.focus()
      }        
    }, */

    beforeOpen (event) {
      console.log(event)
      this.TEMPtime = Date.now() // Set the opening time of the modal
    },

    beforeClose (event) {
      console.log(event)
      // If modal was open less then 5000 ms - prevent closing it
      if (this.TEMPtime + this.TEMPduration < Date.now()) {
        event.stop()
      }
    },

    getDemoOptions() {
      console.log('getDemoOptions() called')
      rpcs.rpc('get_demo_project_options') // Get the current user's framework summaries from the server.
        .then(response => {
          this.demoOptions = response.data // Set the frameworks to what we received.
          this.demoOption = this.demoOptions[0]
          console.log('Loaded demo options:')
          console.log(this.demoOptions)
          console.log(this.demoOption)
        })
        .catch(error => {
          status.failurePopup(this, 'Could not load demo project options: ' + error.message)
        })
    },

    updateFrameworkSummaries() {
      console.log('updateFrameworkSummaries() called')

      // Get the current user's framework summaries from the server.
      rpcs.rpc('load_current_user_framework_summaries')
      .then(response => {
        // Set the frameworks to what we received.
        this.frameworkSummaries = response.data.frameworks

        if (this.frameworkSummaries.length) {
          console.log('Framework summaries found')
          console.log(this.frameworkSummaries)
          this.currentFramework = this.frameworkSummaries[0].framework.name
          console.log('Current framework: '+this.currentFramework)
        } else {
          console.log('No framework summaries found')
        }
      })
      .catch(error => {
        // Failure popup.        
        status.failurePopup(this, 'Could not load frameworks: ' + error.message)
      })  
    },

    projectLoaded(uid) {
      console.log('projectLoaded called')
      if (this.$store.state.activeProject.project != undefined) {
        if (this.$store.state.activeProject.project.id === uid) {
          console.log('Project ' + uid + ' is loaded')
          return true
        } else {
          return false
        }
      } else {
        return false
      }
    },

    updateProjectSummaries(setActiveID) {
      console.log('updateProjectSummaries() called')
      status.start(this)
      rpcs.rpc('load_current_user_project_summaries') // Get the current user's project summaries from the server.
      .then(response => {
        let lastCreationTime = null
        let lastCreatedID = null
        this.projectSummaries = response.data.projects // Set the projects to what we received.
        if (this.projectSummaries.length > 0) { // Initialize the last creation time stuff if we have a non-empty list.
          lastCreationTime = new Date(this.projectSummaries[0].project.creationTime)
          lastCreatedID = this.projectSummaries[0].project.id
        }
        this.projectSummaries.forEach(theProj => { // Preprocess all projects.
          theProj.selected = false // Set to not selected.
          theProj.renaming = '' // Set to not being renamed.
          theProj.project.creationTime = new Date(theProj.project.creationTime) // Extract actual Date objects from the strings.
          theProj.project.updatedTime = new Date(theProj.project.updatedTime)
          if (theProj.project.creationTime >= lastCreationTime) { // Update the last creation time and ID if what se see is later.
            lastCreationTime = theProj.project.creationTime
            lastCreatedID = theProj.project.id
          } 
        }) 
        if (this.projectSummaries.length > 0) { // If we have a project on the list...
          if (setActiveID == null) { // If no ID is passed in, set the active project to the last-created project.
            this.openProject(lastCreatedID)            
          } else { // Otherwise, set the active project to the one passed in.
            this.openProject(setActiveID)
          }
        }
        status.succeed(this, '')  // No green popup.
      })
      .catch(error => {
        status.fail(this, 'Could not load projects: ' + error.message)
      })     
    },

    addDemoProject() {
      console.log('addDemoProject() called')
      this.$modal.hide('demo-project')
      status.start(this)
      rpcs.rpc('add_demo_project', [this.$store.state.currentUser.UID, this.demoOption]) // Have the server create a new project.
      .then(response => {
        this.updateProjectSummaries(response.data.projectId) // Update the project summaries so the new project shows up on the list.
        status.succeed(this, '') // Already have notification from project
      })
      .catch(error => {
        status.fail(this, 'Could not add demo project: ' + error.message)
      })
    },

    addDemoProjectModal() {
      // Open a model dialog for creating a new project
      console.log('addDemoProjectModal() called');
      this.$modal.show('demo-project');
    },

    createNewProjectModal() {
      console.log('createNewProjectModal() called')
      this.$modal.show('create-project')
    },

    // Open a model dialog for creating a progbook
    createProgbookModal(uid) {
      this.activeuid = uid
      let matchProject = this.projectSummaries.find(theProj => theProj.project.id === uid) // Find the project that matches the UID passed in.
      console.log('createProgbookModal() called for ' + matchProject.project.name)
      this.$modal.show('create-progbook');
    },

    createNewProject() {
      console.log('createNewProject() called')
      this.$modal.hide('create-project')
      status.start(this) // Start indicating progress.
      let matchFramework = this.frameworkSummaries.find(theFrame => theFrame.framework.name === this.currentFramework) // Find the project that matches the UID passed in.
      console.log('Loading framework ' + this.currentFramework)
      console.log(matchFramework)
      rpcs.download('create_new_project',  // Have the server create a new project.
        [this.$store.state.currentUser.UID, matchFramework.framework.id, this.proj_name, this.num_pops, this.num_progs, this.data_start, this.data_end])
      .then(response => {
        this.updateProjectSummaries(null) // Update the project summaries so the new project shows up on the list. Note: There's no easy way to get the new project UID to tell the project update to choose the new project because the RPC cannot pass it back.
        status.succeed(this, 'New project "' + this.proj_name + '" created') // Indicate success.
      })
      .catch(error => {
        status.fail(this, 'Could not add new project')    // Indicate failure.
      })  
    },

    uploadProjectFromFile() {
      console.log('uploadProjectFromFile() called')
      rpcs.upload('create_project_from_prj_file', [this.$store.state.currentUser.UID], {}, '.prj') // Have the server upload the project.
      .then(response => {
        status.start(this)  // This line needs to be here to avoid the spinner being up during the user modal.      
        this.updateProjectSummaries(response.data.projectId) // Update the project summaries so the new project shows up on the list.
        status.succeed(this, 'New project uploaded')
      })
      .catch(error => {
        status.fail(this, 'Could not upload file')
      }) 
    },

    projectIsActive(uid) {
      if (this.$store.state.activeProject.project === undefined) { // If the project is undefined, it is not active.
        return false
      } else { // Otherwise, the project is active if the UIDs match.
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
          } else if (this.sortColumn === 'creationTime') {
            return proj1.project.creationTime > proj2.project.creationTime ? sortDir: -sortDir
          } else if (this.sortColumn === 'updatedTime') {
            return proj1.project.updatedTime > proj2.project.updatedTime ? sortDir: -sortDir
          }
        }
      )
    },



    openProject(uid) {
      // Find the project that matches the UID passed in.
      let matchProject = this.projectSummaries.find(theProj => theProj.project.id === uid)
      console.log('openProject() called for ' + matchProject.project.name)
      this.$store.commit('newActiveProject', matchProject) // Set the active project to the matched project.
      status.successPopup(this, 'Project "'+matchProject.project.name+'" loaded') // Success popup.
    },

    copyProject(uid) {
      let matchProject = this.projectSummaries.find(theProj => theProj.project.id === uid) // Find the project that matches the UID passed in.
      console.log('copyProject() called for ' + matchProject.project.name)
      status.start(this) // Start indicating progress.
      rpcs.rpc('copy_project', [uid]) // Have the server copy the project, giving it a new name.
      .then(response => {
        this.updateProjectSummaries(response.data.projectId) // Update the project summaries so the copied program shows up on the list.
        status.succeed(this, 'Project "'+matchProject.project.name+'" copied')    // Indicate success.
      })
      .catch(error => {
        status.fail(this, 'Could not copy project: ' + error.message) // Indicate failure.
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
        status.start(this)
        
        // Have the server change the name of the project by passing in the new copy of the
        // summary.
        rpcs.rpc('update_project_from_summary', [newProjectSummary])
        .then(response => {
          // Update the project summaries so the rename shows up on the list.
          this.updateProjectSummaries(newProjectSummary.project.id)

          // Turn off the renaming mode.
          projectSummary.renaming = ''
          
          // Indicate success.
          status.succeed(this, '')  // No green popup message.          
        })
        .catch(error => {
          // Indicate failure.
          status.fail(this, 'Could not rename project')    
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
      status.start(this)
        
      // Make the server call to download the project to a .prj file.
      rpcs.download('download_project', [uid])
      .then(response => {
        // Indicate success.
        status.succeed(this, '')  // No green popup message.        
      })
      .catch(error => {
        // Indicate failure.
        status.fail(this, 'Could not download project')      
      })
    },

    downloadFramework(uid) {
      // Find the project that matches the UID passed in.
      let matchProject = this.projectSummaries.find(theProj => theProj.project.id === uid)
      console.log('downloadFramework() called for ' + matchProject.project.name)
      status.start(this, 'Downloading framework...') // Start indicating progress.
      rpcs.download('download_framework_from_project', [uid])
        .then(response => {
          status.succeed(this, '')  // No green popup message.
        })
        .catch(error => {
          status.fail(this, 'Could not download framework: ' + error.message) // Indicate failure.
        })
    },

    downloadDatabook(uid) {
      // Find the project that matches the UID passed in.
      let matchProject = this.projectSummaries.find(theProj => theProj.project.id === uid)
      console.log('downloadDatabook() called for ' + matchProject.project.name)
      status.start(this, 'Downloading data book...') // Start indicating progress.
      rpcs.download('download_databook', [uid])
        .then(response => {
          status.succeed(this, '')  // No green popup message.
        })
        .catch(error => {
          // Indicate failure.
          status.fail(this, 'Could not download databook: ' + error.message)
        })
    },

    downloadProgbook(uid) {
      // Find the project that matches the UID passed in.
      let matchProject = this.projectSummaries.find(theProj => theProj.project.id === uid)
      console.log('downloadProgbook() called for ' + matchProject.project.name)
      status.start(this, 'Downloading program book...') // Start indicating progress.
      rpcs.download('download_progbook', [uid])
      .then(response => {
        status.succeed(this, '')  // No green popup message.
      })
      .catch(error => {
        // Indicate failure.
        status.fail(this, 'Could not download program book: ' + error.message)
      })      
    },

    createProgbook() {
      // Find the project that matches the UID passed in.
      let uid = this.activeuid
      let matchProject = this.projectSummaries.find(theProj => theProj.project.id === uid)
      console.log('createProgbook() called for ' + matchProject.project.name)
      this.$modal.hide('create-progbook')
      status.start(this, 'Creating program book...') // Start indicating progress.
      rpcs.download('create_progbook', [uid, this.num_progs])
        .then(response => {
          status.succeed(this, '')  // No green popup message.
        })
        .catch(error => {
          // Indicate failure.
          status.fail(this, 'Could not create program book: ' + error.message)
        })
    },

    uploadDatabook(uid) {
      let matchProject = this.projectSummaries.find(theProj => theProj.project.id === uid) // Find the project that matches the UID passed in.
      console.log('uploadDatabook() called for ' + matchProject.project.name)
      rpcs.upload('upload_databook', [uid], {})
      .then(response => {
        status.start(this)  // This line needs to be here to avoid the spinner being up during the user modal.
        this.updateProjectSummaries(uid) // Update the project summaries so the copied program shows up on the list.
        status.succeed(this, 'Data uploaded to project "'+matchProject.project.name+'"') // Indicate success.
      })
      .catch(error => {
        status.fail(this, 'Could not upload data: ' + error.message) // Indicate failure.
      })
    },

    uploadProgbook(uid) {
      // Find the project that matches the UID passed in.
      let matchProject = this.projectSummaries.find(theProj => theProj.project.id === uid)
      console.log('uploadProgbook() called for ' + matchProject.project.name)
      rpcs.upload('upload_progbook', [uid], {})
      .then(response => {
        status.start(this)  // This line needs to be here to avoid the spinner being up during the user modal.
        this.updateProjectSummaries(uid) // Update the project summaries so the copied program shows up on the list.
        status.succeed(this, 'Programs uploaded to project "'+matchProject.project.name+'"')   // Indicate success.
      })
      .catch(error => {
        status.fail(this, 'Could not upload progbook: ' + error.message) // Indicate failure.
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
        status.start(this)
      
        rpcs.rpc('delete_projects', [selectProjectsUIDs])
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
          status.succeed(this, '')  // No green popup message.
        })
        .catch(error => {
          // Indicate failure.
          status.fail(this, 'Could not delete project/s')     
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
        status.start(this)
        
        rpcs.download('load_zip_of_prj_files', [selectProjectsUIDs])
        .then(response => {
          // Indicate success.
          status.succeed(this, '')  // No green popup message.         
        })
        .catch(error => {
          // Indicate failure.
          status.fail(this, 'Could not download project/s')     
        })       
      }
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang="scss" scoped>
</style>
