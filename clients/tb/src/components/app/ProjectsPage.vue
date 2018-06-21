<!--
Manage projects page

Last update: 2018-05-29
-->

<template>
  <div class="SitePage">
    <div class="PageSection">

      <div class="ControlsRow">
        <button class="btn" @click="addDemoProject">Add demo project</button>
        &nbsp; &nbsp;
        <button class="btn" @click="createNewProjectModal">Create blank project</button>
        &nbsp; &nbsp;
        <button class="btn" @click="uploadProjectFromFile">Upload project from file</button>
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
            <th>Select</th>
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
            <th>Actions</th>
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
            </td>
<!--            <td>{{ projectSummary.country }}</td> -->
            <td>{{ projectSummary.project.creationTime }}</td>
            <td>{{ projectSummary.project.updatedTime ? projectSummary.project.updatedTime:
              'No modification' }}</td>
            <td style="white-space: nowrap">
              <button class="btn" @click="copyProject(projectSummary.project.id)">Copy</button>
              <button class="btn" @click="renameProject(projectSummary)">Rename</button>
              <button class="btn" @click="downloadProjectFile(projectSummary.project.id)">Download</button>
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
            Create project and download data entry spreadsheet
          </button>

          <button @click="$modal.hide('create-project')" class='btn __red' style="display:inline-block">
            Cancel
          </button>
        </div>
      </div>


      <div>

      </div>
    </modal>
  </div>

</template>

<script>
import axios from 'axios'
var filesaver = require('file-saver')
import rpcservice from '@/services/rpc-service'
import router from '@/router'

export default {
  name: 'ProjectsPage',

  data() {
    return {
      filterPlaceholder: 'Type here to filter projects', // Placeholder text for table filter box
      filterText: '',  // Text in the table filter box
      allSelected: false, // Are all of the projects selected?
      sortColumn: 'name',  // Column of table used for sorting the projects: name, country, creationTime, updatedTime, dataUploadTime
      sortReverse: false, // Sort in reverse order?
      projectSummaries: [], // List of summary objects for projects the user has
      proj_name: '', // For creating a new project: number of populations
      num_pops: 5, // For creating a new project: number of populations
      data_start: 2000, // For creating a new project: number of populations
      data_end: 2020, // For creating a new project: number of populations
    }
  },

  computed: {
    sortedFilteredProjectSummaries() {
      return this.applyNameFilter(this.applySorting(this.projectSummaries))
//      return this.applyNameFilter(this.applySorting(this.applyCountryFilter(this.projectSummaries)))
    }
  },

  created() {
    // If we have no user logged in, automatically redirect to the login page.
    if (this.$store.state.currentUser.displayname == undefined) {
      router.push('/login')
    }

    // Otherwise...
    else {
      // Load the project summaries of the current user.
      this.updateProjectSummaries()

      // Initialize the countryList by picking out the (unique) country names.
      // (First, a list is constructed pulling out the non-unique countries
      // for each project, then this array is stuffed into a new Set (which
      // will not duplicate array entries) and then the spread operator is
      // used to pull the set items out into an array.)
//      this.countryList = [...new Set(this.projectSummaries.map(theProj => theProj.country))]

      // Initialize the selection of the demo project to the first element.
//      this.selectedCountry = 'Select country...'
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

    updateProjectSummaries() {
      console.log('updateProjectSummaries() called')

      // Get the current user's project summaries from the server.
      rpcservice.rpcCall('load_current_user_project_summaries')
      .then(response => {
        // Set the projects to what we received.
        this.projectSummaries = response.data.projects

        // Set select flags for false initially.
        this.projectSummaries.forEach(theProj => {
		      theProj.selected = false
		      theProj.renaming = ''
		    })
      })
    },

    addDemoProject() {
      console.log('addDemoProject() called')

      // Have the server create a new project.
      rpcservice.rpcCall('add_demo_project', [this.$store.state.currentUser.UID])
        .then(response => {
          // Update the project summaries so the new project shows up on the list.
          this.updateProjectSummaries()

          this.$notifications.notify({
            message: 'Demo project added',
            icon: 'ti-check',
            type: 'success',
            verticalAlign: 'top',
            horizontalAlign: 'center',
          });
        })
    },

    createNewProjectModal() {

      this.$modal.show('create-project');

    },



    createNewProject() {
      console.log('createNewProject() called')
      this.$modal.hide('create-project')

      // Have the server create a new project.
      rpcservice.rpcCall('create_new_project', [this.$store.state.currentUser.UID])
      .then(response => {
        // Update the project summaries so the new project shows up on the list.
        this.updateProjectSummaries()

        this.$notifications.notify({
          message: 'New project created',
          icon: 'ti-check',
          type: 'success',
          verticalAlign: 'top',
          horizontalAlign: 'center',
        });
      })
    },

    uploadProjectFromFile() {
      console.log('uploadProjectFromFile() called')

      // Have the server upload the project.
      rpcservice.rpcUploadCall('create_project_from_prj_file', [this.$store.state.currentUser.UID], {})
      .then(response => {
        // Update the project summaries so the new project shows up on the list.
        this.updateProjectSummaries()
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
      return projects.sort((proj1, proj2) =>
        {
          let sortDir = this.sortReverse ? -1: 1
          if (this.sortColumn === 'name') {
            return (proj1.project.name > proj2.project.name ? sortDir: -sortDir)
          }
/*          else if (this.sortColumn === 'country') {
            return proj1.country > proj2.country ? sortDir: -sortDir
          } */
          else if (this.sortColumn === 'creationTime') {
            return proj1.project.creationTime > proj2.project.creationTime ? sortDir: -sortDir
          }
          else if (this.sortColumn === 'updatedTime') {
            return proj1.project.updateTime > proj2.project.updateTime ? sortDir: -sortDir
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

      // Set the active project to the matched project.
      this.$store.commit('newActiveProject', matchProject)

      this.$notifications.notify({
        message: 'Project "'+matchProject.project.name+'" loaded',
        icon: 'ti-check',
        type: 'success',
        verticalAlign: 'top',
        horizontalAlign: 'center',
      });
    },

    copyProject(uid) {
      // Find the project that matches the UID passed in.
      let matchProject = this.projectSummaries.find(theProj => theProj.project.id === uid)

      console.log('copyProject() called for ' + matchProject.project.name)

	    // Have the server copy the project, giving it a new name.
      rpcservice.rpcCall('copy_project', [uid])
      .then(response => {
        // Update the project summaries so the copied program shows up on the list.
        this.updateProjectSummaries()
      })

      this.$notifications.notify({
        message: 'Project "'+matchProject.project.name+'" copied',
        icon: 'ti-check',
        type: 'success',
        verticalAlign: 'top',
        horizontalAlign: 'center',
      });
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

        // Have the server change the name of the project by passing in the new copy of the
        // summary.
        rpcservice.rpcCall('update_project_from_summary', [newProjectSummary])
        .then(response => {
          // Update the project summaries so the rename shows up on the list.
          this.updateProjectSummaries()

		      // Turn off the renaming mode.
		      projectSummary.renaming = ''
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

	    // Make the server call to download the project to a .prj file.
      rpcservice.rpcDownloadCall('download_project', [uid])
    },

  // Confirmation alert
    deleteModal() {
      // Alert object data
      var obj = {
            message: 'Are you sure you want to delete the selected projects?',
            useConfirmBtn: true,
            customConfirmBtnClass: 'btn __red',
            customCloseBtnClass: 'btn',
            onConfirm: this.deleteSelectedProjects
          }
      this.$Simplert.open(obj)
    },

    deleteSelectedProjects() {
      // Pull out the names of the projects that are selected.
      let selectProjectsUIDs = this.projectSummaries.filter(theProj =>
        theProj.selected).map(theProj => theProj.project.id)

      console.log('deleteSelectedProjects() called for ', selectProjectsUIDs)

      // Have the server delete the selected projects.
	    if (selectProjectsUIDs.length > 0) {
        rpcservice.rpcCall('delete_projects', [selectProjectsUIDs])
        .then(response => {
          // Update the project summaries so the deletions show up on the list.
          this.updateProjectSummaries()
        })
	    }
    },

    downloadSelectedProjects() {
      // Pull out the names of the projects that are selected.
      let selectProjectsUIDs = this.projectSummaries.filter(theProj =>
        theProj.selected).map(theProj => theProj.project.id)

      console.log('deleteSelectedProjects() called for ', selectProjectsUIDs)

      // Have the server download the selected projects.
	    if (selectProjectsUIDs.length > 0)
        rpcservice.rpcDownloadCall('load_zip_of_prj_files', [selectProjectsUIDs])
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<!--<style lang="scss" scoped>-->
<!--</style>-->
<style>
  .vue-dialog div {
    box-sizing: border-box;
  }
  .vue-dialog .dialog-flex {
    width: 100%;
    height: 100%;
  }
  .vue-dialog .dialog-content {
    flex: 1 0 auto;
    width: 100%;
    padding: 15px;
    font-size: 14px;
  }
  .vue-dialog .dialog-c-title {
    font-weight: 600;
    padding-bottom: 15px;
  }
  .vue-dialog .dialog-c-text {
  }
  .vue-dialog .vue-dialog-buttons {
    display: flex;
    flex: 0 1 auto;
    width: 100%;
    border-top: 1px solid #eee;
  }
  .vue-dialog .vue-dialog-buttons-none {
    width: 100%;
    padding-bottom: 15px;
  }
  .vue-dialog-button {
    font-size: 12px !important;
    background: transparent;
    padding: 0;
    margin: 0;
    border: 0;
    cursor: pointer;
    box-sizing: border-box;
    line-height: 40px;
    height: 40px;
    color: inherit;
    font: inherit;
    outline: none;
  }
  .vue-dialog-button:hover {
    background: rgba(0, 0, 0, 0.01);
  }
  .vue-dialog-button:active {
    background: rgba(0, 0, 0, 0.025);
  }
  .vue-dialog-button:not(:first-of-type) {
    border-left: 1px solid #eee;
  }
</style>
