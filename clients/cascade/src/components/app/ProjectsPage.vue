<!--
Manage projects page

Last update: 2018-05-29
-->

<template>
  <div class="SitePage">
    <div class="PageSection">

      <div class="ControlsRow">
        <button class="btn" @click="createNewProject">Create new project</button>
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
 <!--           <th @click="updateSorting('country')" class="sortable">
              Country
              <span v-show="sortColumn == 'country' && !sortReverse">
                <i class="fas fa-caret-down"></i>
              </span>
              <span v-show="sortColumn == 'country' && sortReverse">
                <i class="fas fa-caret-up"></i>
              </span>
              <span v-show="sortColumn != 'country'">
                <i class="fas fa-caret-up" style="visibility: hidden"></i>
              </span>
            </th> -->
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
<!--          <tr>
            <td>
              <button class="btn" @click="createNewProject">Create new project</button>
            </td>
<!-- comment out for now            <td>
              <select v-model="selectedCountry">
                <option>Select country...</option>
                <option v-for="choice in countryList">
                  {{ choice }}
                </option>
              </select>
            </td>
          </tr> -->
        </tbody>
      </table>

      <div class="ControlsRow">
        <button class="btn" @click="deleteModal()">Delete selected</button>
        &nbsp; &nbsp;
        <button class="btn" @click="downloadSelectedProjects">Download selected</button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
var filesaver = require('file-saver')
import rpcservice from '@/services/rpc-service'
import router from '@/router'
//import PaperNotification from './components/generic/NotificationPlugin/Notification.vue'
//import PaperNotification from './components/generic/NotificationPlugin'

export default {
  name: 'ProjectsPage',

  data() {
    return {
      // List of projects to choose from (by project name)
      demoProjectList: [],

      // Selected demo project (by name)
      selectedDemoProject: '',

      // List of demo project summaries
      demoProjectSummaries: [],

      // Placeholder text for table filter box
      filterPlaceholder: 'Type here to filter projects',

      // Text in the table filter box
      filterText: '',

      // Are all of the projects selected?
      allSelected: false,

      // Column of table used for sorting the projects
      sortColumn: 'name',  // name, country, creationTime, updatedTime, dataUploadTime

      // Sort in reverse order?
      sortReverse: false,

/* old project summaries stuff to get rid of
        // List of summary objects for projects the user has
        projectSummaries:
        [
          {
            projectName: 'Afghanistan test 1',
            country: 'Afghanistan',
            creationTime: '2017-Jun-01 02:45 AM',
            updateTime: '2017-Jun-02 05:41 AM',
            uid: 1
          },
          {
            projectName: 'Afghanistan HBP equity',
            country: 'Afghanistan',
            creationTime: '2017-Jun-03 03:12 PM',
            updateTime: '2017-Jun-05 03:38 PM',
            uid: 2
          },
          {
            projectName: 'Final Afghanistan HBP',
            country: 'Afghanistan',
            creationTime: '2017-Jun-06 08:15 PM',
            updateTime: '2017-Jun-06 08:20 PM',
            uid: 3
          },
          {
            projectName: 'Pakistan test 1',
            country: 'Pakistan',
            creationTime: '2017-Sep-21 08:44 AM',
            updateTime: '2017-Sep-21 08:44 AM',
            uid: 4
          }
        ], */

      // List of summary objects for projects the user has
      projectSummaries: [],

      // Available countries
      countryList: [],

      // Country selected in the bottom select box
      selectedCountry: 'Select country'
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

      // Get the demo project summaries from the server.
/*      rpcservice.rpcCall('get_scirisdemo_projects')
      .then(response => {
        // Set the demo projects to what we received.
        this.demoProjectSummaries = response.data.projects

        // Initialize the demoProjectList by picking out the project names.
        this.demoProjectList = this.demoProjectSummaries.map(demoProj => demoProj.project.name)

        // Initialize the selection of the demo project to the first element.
        this.selectedDemoProject = this.demoProjectList[0]
      }) */
    },

/*    addDemoProject() {
      console.log('addDemoProject() called')

      // Find the object in the default project summaries that matches what's
      // selected in the select box.
      let foundProject = this.demoProjectSummaries.find(demoProj =>
        demoProj.project.name == this.selectedDemoProject)

      // Make a deep copy of the found object by JSON-stringifying the old
      // object, and then parsing the result back into a new object.
      let newProject = JSON.parse(JSON.stringify(foundProject));

      // Push the deep copy to the projectSummaries list.
//      this.projectSummaries.push(newProject)

//      this.projectSummaries.push(this.demoProjectSummaries[0])
    }, */

    createNewProject() {
      console.log('createNewProject() called')

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
<style lang="scss" scoped>
</style>
