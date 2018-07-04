<!--
Manage frameworks page

Last update: 2018-05-29
-->

<template>
  <div class="SitePage">
    <div class="PageSection">

      <div class="ControlsRow">
        <button class="btn __blue" @click="addDemoFrameworkModal">Load framework from library</button>
        &nbsp; &nbsp;
        <button class="btn __blue" @click="createNewFrameworkModal">Create new framework</button>
        &nbsp; &nbsp;
        <button class="btn __blue" @click="uploadFrameworkFromFile">Upload framework from file</button>
        &nbsp; &nbsp;
      </div>
    </div>

    <div class="PageSection"
         v-if="frameworkSummaries.length > 0">
      <!--<h2>Manage frameworks</h2>-->

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
          <th>Framework actions</th>
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
          <th>Framework book</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="frameworkSummary in sortedFilteredFrameworkSummaries"
            :class="{ highlighted: frameworkIsActive(frameworkSummary.framework.id) }">
          <td>
            <input type="checkbox" @click="uncheckSelectAll()" v-model="frameworkSummary.selected"/>
          </td>
          <td v-if="frameworkSummary.renaming !== ''">
            <input type="text"
                   class="txbox"
                   @keyup.enter="renameFramework(frameworkSummary)"
                   v-model="frameworkSummary.renaming"/>
          </td>
          <td v-else>
            {{ frameworkSummary.framework.name }}
          </td>
          <td>
            <button class="btn __green" @click="openFramework(frameworkSummary.framework.id)">Open</button>
            <button class="btn" @click="copyFramework(frameworkSummary.framework.id)">Copy</button>
            <button class="btn" @click="renameFramework(frameworkSummary)">Rename</button>
            <button class="btn" @click="downloadFrameworkFile(frameworkSummary.framework.id)">Download</button>
          </td>
          <td>{{ frameworkSummary.framework.creationTime }}</td>
          <td>{{ frameworkSummary.framework.updatedTime ? frameworkSummary.framework.updatedTime:
            'No modification' }}</td>
          <td>
            <button class="btn __blue" @click="uploadFrameworkbook(frameworkSummary.framework.id)">Upload</button>
            <button class="btn" @click="downloadFrameworkbook(frameworkSummary.framework.id)">Download</button>
          </td>
        </tr>
        </tbody>
      </table>

      <div class="ControlsRow">
        <button class="btn" @click="deleteModal()">Delete selected</button>
        &nbsp; &nbsp;
        <button class="btn" @click="downloadSelectedFrameworks">Download selected</button>
      </div>
    </div>

    <modal name="demo-framework"
           height="auto"
           :classes="['v--modal', 'vue-dialog']"
           :width="width"
           :pivot-y="0.3"
           :adaptive="true"
           :clickToClose="clickToClose"
           :transition="transition">

      <div class="dialog-content">
        <div class="dialog-c-title">
          Load framework from library
        </div>
        <div class="dialog-c-text">
          <select v-model="currentFramework">
            <option v-for='framework in frameworkOptions'>
              {{ framework }}
            </option>
          </select><br><br>
        </div>
        <div style="text-align:justify">
          <button @click="addDemoFramework()" class='btn __green' style="display:inline-block">
            Add selected
          </button>

          <button @click="$modal.hide('demo-framework')" class='btn __red' style="display:inline-block">
            Cancel
          </button>
        </div>
      </div>
    </modal>

    <modal name="create-framework"
           height="auto"
           :classes="['v--modal', 'vue-dialog']"
           :width="width"
           :pivot-y="0.3"
           :adaptive="true"
           :clickToClose="clickToClose"
           :transition="transition">

      <div class="dialog-content">
        <div class="dialog-c-title">
          Create new framework
        </div>
        <div class="dialog-c-text">
          Name:<br>
          <input type="text"
                 class="txbox"
                 v-model="frame_name"/><br>
          Number of compartments:<br>
          <input type="text"
                 class="txbox"
                 v-model="num_comps"/><br>
        </div>
        <div style="text-align:justify">
          <button @click="createNewFramework()" class='btn __green' style="display:inline-block">
            Create
          </button>

          <button @click="$modal.hide('create-framework')" class='btn __red' style="display:inline-block">
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
  import rpcservice from '@/services/rpc-service'
  import router from '@/router'

  export default {
    name: 'FrameworksPage',

    data() {
      return {
        filterPlaceholder: 'Type here to filter frameworks', // Placeholder text for table filter box
        filterText: '',  // Text in the table filter box
        allSelected: false, // Are all of the frameworks selected?
        sortColumn: 'name',  // Column of table used for sorting the frameworks: name, country, creationTime, updatedTime, dataUploadTime
        sortReverse: false, // Sort in reverse order?
        frameworkSummaries: [], // List of summary objects for frameworks the user has
        frame_name: 'Default', // For creating a new framework: number of populations
        num_comps: 5, // For creating a new framework: number of populations
        frameworkOptions: ['SIR model', 'Tuberculosis', 'Diabetes', 'Service delivery'],
        currentFramework: 'Service delivery'

      }
    },

    computed: {
      sortedFilteredFrameworkSummaries() {
        return this.applyNameFilter(this.applySorting(this.frameworkSummaries))
//      return this.applyNameFilter(this.applySorting(this.applyCountryFilter(this.frameworkSummaries)))
      }
    },

    created() {
      // If we have no user logged in, automatically redirect to the login page.
      if (this.$store.state.currentUser.displayname == undefined) {
        router.push('/login')
      }

      // Otherwise...
      else {
        // Load the framework summaries of the current user.
        this.updateFrameworkSummaries()
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

      updateFrameworkSummaries() {
        console.log('updateFrameworkSummaries() called')

        // Get the current user's framework summaries from the server.
        rpcservice.rpcCall('load_current_user_framework_summaries')
          .then(response => {
            // Set the frameworks to what we received.
            this.frameworkSummaries = response.data.frameworks

            // Set select flags for false initially.
            this.frameworkSummaries.forEach(theFrame => {
              theFrame.selected = false
              theFrame.renaming = ''
            })
          })
      },

      addDemoFramework() {
        console.log('addDemoFramework() called')
        this.$modal.hide('demo-framework')
        // Have the server create a new framework.
        rpcservice.rpcCall('add_demo_framework', [this.$store.state.currentUser.UID, this.currentFramework])
          .then(response => {
            // Update the framework summaries so the new framework shows up on the list.
            this.updateFrameworkSummaries()

            this.$notifications.notify({
              message: 'Library framework "'+which+'" loaded',
              icon: 'ti-check',
              type: 'success',
              verticalAlign: 'top',
              horizontalAlign: 'center',
            });
          })
      },

      addDemoFrameworkModal() {
        // Open a model dialog for creating a new framework
        console.log('addDemoFrameworkModal() called');
        this.$modal.show('demo-framework');
      },

      createNewFrameworkModal() {
        // Open a model dialog for creating a new framework
        console.log('createNewFrameworkModal() called');
        this.$modal.show('create-framework');
      },


      createNewFramework() {
        console.log('createNewFramework() called')
        this.$modal.hide('create-framework')

        // Have the server create a new framework.
        rpcservice.rpcDownloadCall('create_new_framework', [this.$store.state.currentUser.UID, this.frame_name, this.num_comps])
          .then(response => {
            // Update the framework summaries so the new framework shows up on the list.
            this.updateFrameworkSummaries()

            this.$notifications.notify({
              message: 'New framework "'+this.frame_name+'" created',
              icon: 'ti-check',
              type: 'success',
              verticalAlign: 'top',
              horizontalAlign: 'center',
            });
          })
      },

      uploadFrameworkFromFile() {
        console.log('uploadFrameworkFromFile() called')

        // Have the server upload the framework.
        rpcservice.rpcUploadCall('create_framework_from_frw_file', [this.$store.state.currentUser.UID], {}, '.frw')
          .then(response => {
            // Update the framework summaries so the new framework shows up on the list.
            this.updateFrameworkSummaries()
          })
      },

      frameworkIsActive(uid) {
        // If the framework is undefined, it is not active.
        if (this.$store.state.activeFramework.framework === undefined) {
          return false
        }

        // Otherwise, the framework is active if the UIDs match.
        else {
          return (this.$store.state.activeFramework.framework.id === uid)
        }
      },

      selectAll() {
        console.log('selectAll() called')

        // For each of the frameworks, set the selection of the framework to the
        // _opposite_ of the state of the all-select checkbox's state.
        // NOTE: This function depends on it getting called before the
        // v-model state is updated.  If there are some cases of Vue
        // implementation where these happen in the opposite order, then
        // this will not give the desired result.
        this.frameworkSummaries.forEach(theFramework => theFramework.selected = !this.allSelected)
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

      applyNameFilter(frameworks) {
        return frameworks.filter(theFramework => theFramework.framework.name.toLowerCase().indexOf(this.filterText.toLowerCase()) !== -1)
      },

      applySorting(frameworks) {
        return frameworks.sort((proj1, proj2) =>
          {
            let sortDir = this.sortReverse ? -1: 1
            if (this.sortColumn === 'name') {
              return (proj1.framework.name > proj2.framework.name ? sortDir: -sortDir)
            }
            /*          else if (this.sortColumn === 'country') {
             return proj1.country > proj2.country ? sortDir: -sortDir
             } */
            else if (this.sortColumn === 'creationTime') {
              return proj1.framework.creationTime > proj2.framework.creationTime ? sortDir: -sortDir
            }
            else if (this.sortColumn === 'updatedTime') {
              return proj1.framework.updateTime > proj2.framework.updateTime ? sortDir: -sortDir
            }
          }
        )
      },

      /*    applyCountryFilter(frameworks) {
       if (this.selectedCountry === 'Select country...')
       return frameworks
       else
       return frameworks.filter(theFrame => theFrame.country === this.selectedCountry)
       }, */

      openFramework(uid) {
        // Find the framework that matches the UID passed in.
        let matchFramework = this.frameworkSummaries.find(theFrame => theFrame.framework.id === uid)

        console.log('openFramework() called for ' + matchFramework.framework.name)

        // Set the active framework to the matched framework.
        this.$store.commit('newActiveFramework', matchFramework)

        this.$notifications.notify({
          message: 'Framework "'+matchFramework.framework.name+'" loaded',
          icon: 'ti-check',
          type: 'success',
          verticalAlign: 'top',
          horizontalAlign: 'center',
        });
      },

      copyFramework(uid) {
        // Find the framework that matches the UID passed in.
        let matchFramework = this.frameworkSummaries.find(theFrame => theFrame.framework.id === uid)

        console.log('copyFramework() called for ' + matchFramework.framework.name)

        // Have the server copy the framework, giving it a new name.
        rpcservice.rpcCall('copy_framework', [uid])
          .then(response => {
            // Update the framework summaries so the copied program shows up on the list.
            this.updateFrameworkSummaries()
          })

        this.$notifications.notify({
          message: 'Framework "'+matchFramework.framework.name+'" copied',
          icon: 'ti-check',
          type: 'success',
          verticalAlign: 'top',
          horizontalAlign: 'center',
        });
      },

      renameFramework(frameworkSummary) {
        console.log('renameFramework() called for ' + frameworkSummary.framework.name)

        // If the framework is not in a mode to be renamed, make it so.
        if (frameworkSummary.renaming === '') {
          frameworkSummary.renaming = frameworkSummary.framework.name
        }

        // Otherwise (it is to be renamed)...
        else {
          // Make a deep copy of the frameworkSummary object by JSON-stringifying the old
          // object, and then parsing the result back into a new object.
          let newFrameworkSummary = JSON.parse(JSON.stringify(frameworkSummary))

          // Rename the framework name in the client list from what's in the textbox.
          newFrameworkSummary.framework.name = frameworkSummary.renaming

          // Have the server change the name of the framework by passing in the new copy of the
          // summary.
          rpcservice.rpcCall('update_framework_from_summary', [newFrameworkSummary])
            .then(response => {
              // Update the framework summaries so the rename shows up on the list.
              this.updateFrameworkSummaries()

              // Turn off the renaming mode.
              frameworkSummary.renaming = ''
            })
        }

        // This silly hack is done to make sure that the Vue component gets updated by this function call.
        // Something about resetting the framework name informs the Vue component it needs to
        // update, whereas the renaming attribute fails to update it.
        // We should find a better way to do this.
        let theName = frameworkSummary.framework.name
        frameworkSummary.framework.name = 'newname'
        frameworkSummary.framework.name = theName
      },

      downloadFrameworkFile(uid) {
        // Find the framework that matches the UID passed in.
        let matchFramework = this.frameworkSummaries.find(theFrame => theFrame.framework.id === uid)

        console.log('downloadFrameworkFile() called for ' + matchFramework.framework.name)

        // Make the server call to download the framework to a .prj file.
        rpcservice.rpcDownloadCall('download_framework', [uid])
      },

      downloadFrameworkbook(uid) {
        this.$notifications.notify({
          message: 'This is not yet implemented, please check back soon.',
          icon: 'ti-face-sad',
          type: 'warning',
          verticalAlign: 'top',
          horizontalAlign: 'center',
        });

//        let matchFramework = this.frameworkSummaries.find(theFrame => theFrame.framework.id === uid) // Find the framework that matches the UID passed in.
//        console.log('downloadDatabook() called for ' + matchFramework.framework.name)
//        rpcservice.rpcDownloadCall('download_databook', [uid]) // Make the server call to download the framework to a .prj file.
      },


      downloadDefaults(uid) {
        // Find the framework that matches the UID passed in.
        let matchFramework = this.frameworkSummaries.find(theFrame => theFrame.framework.id === uid)

        console.log('downloadDefaults() called for ' + matchFramework.framework.name)

        // Make the server call to download the framework to a .prj file.
        rpcservice.rpcDownloadCall('download_defaults', [uid])
      },

      uploadFrameworkbook(uid) {
        // Find the framework that matches the UID passed in.
        let matchFramework = this.frameworkSummaries.find(theFrame => theFrame.framework.id === uid)

        console.log('uploadFrameworkbook() called for ' + matchFramework.framework.name)

        // Have the server copy the framework, giving it a new name.
        rpcservice.rpcUploadCall('upload_frameworkbook', [uid], {})
          .then(response => {
            // Update the framework summaries so the copied program shows up on the list.
            this.updateFrameworkSummaries()
          })

        this.$notifications.notify({
          message: 'Data uploaded to framework "'+matchFramework.framework.name+'"',
          icon: 'ti-check',
          type: 'success',
          verticalAlign: 'top',
          horizontalAlign: 'center',
        });
      },

      // Confirmation alert
      deleteModal() {
        // Alert object data
        var obj = {
          message: 'Are you sure you want to delete the selected frameworks?',
          useConfirmBtn: true,
          customConfirmBtnClass: 'btn __red',
          customCloseBtnClass: 'btn',
          onConfirm: this.deleteSelectedFrameworks
        }
        this.$Simplert.open(obj)
      },

      deleteSelectedFrameworks() {
        // Pull out the names of the frameworks that are selected.
        let selectFrameworksUIDs = this.frameworkSummaries.filter(theFrame =>
          theFrame.selected).map(theFrame => theFrame.framework.id)

        console.log('deleteSelectedFrameworks() called for ', selectFrameworksUIDs)

        // Have the server delete the selected frameworks.
        if (selectFrameworksUIDs.length > 0) {
          rpcservice.rpcCall('delete_frameworks', [selectFrameworksUIDs])
            .then(response => {
              // Update the framework summaries so the deletions show up on the list.
              this.updateFrameworkSummaries()
            })
        }
      },

      downloadSelectedFrameworks() {
        // Pull out the names of the frameworks that are selected.
        let selectFrameworksUIDs = this.frameworkSummaries.filter(theFrame =>
          theFrame.selected).map(theFrame => theFrame.framework.id)

        console.log('deleteSelectedFrameworks() called for ', selectFrameworksUIDs)

        // Have the server download the selected frameworks.
        if (selectFrameworksUIDs.length > 0)
          rpcservice.rpcDownloadCall('load_zip_of_frw_files', [selectFrameworksUIDs])
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
