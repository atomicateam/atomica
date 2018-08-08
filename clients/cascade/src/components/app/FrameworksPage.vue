<!--
Manage frameworks page

Last update: 2018-08-07
-->

<template>
  <div>
    <div class="PageSection">

      <div class="ControlsRow">
        <button class="btn __blue" @click="addDemoFrameworkModal">Load framework from library</button>
        &nbsp; &nbsp;
        <button class="btn __blue" @click="createNewFramework">Create new framework</button>
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
        </tr>
        </thead>
        <tbody>
<!--        <tr v-for="frameworkSummary in sortedFilteredFrameworkSummaries"
            :class="{ highlighted: frameworkIsActive(frameworkSummary.framework.id) }">  -->      
        <tr v-for="frameworkSummary in sortedFilteredFrameworkSummaries">
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
            <button class="btn" @click="renameFramework(frameworkSummary)" data-tooltip="Rename">
              <i class="ti-pencil"></i>
            </button>
            <button class="btn" @click="copyFramework(frameworkSummary.framework.id)" data-tooltip="Copy">
              <i class="ti-files"></i>
            </button>

            <button class="btn" @click="downloadFrameworkFile(frameworkSummary.framework.id)" data-tooltip="Download">
              <i class="ti-download"></i>
            </button>
          </td>
          <td>{{ frameworkSummary.framework.creationTime.toUTCString() }}</td>
          <td>{{ frameworkSummary.framework.updatedTime ? frameworkSummary.framework.updatedTime.toUTCString():
            'No modification' }}</td>
        </tr>
        </tbody>
      </table>

      <div class="ControlsRow">
        <button class="btn" @click="deleteModal()">Delete selected</button>
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
        <p>
          <a href="https://docs.google.com/document/d/18zgBsP95ThjrDm2Uzzw9aS_jN1ykADAEkGKtif0qvPY/edit?usp=sharing" target="_blank">Framework details</a>
        </p>
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

    <!-- Popup spinner -->
    <popup-spinner></popup-spinner>
    
  </div>

</template>

<script>
  import axios from 'axios'
  var filesaver = require('file-saver')
  import rpcservice from '@/services/rpc-service'
  import status from '@/services/status-service'
  import router from '@/router'
  import PopupSpinner from './Spinner.vue'
  
  export default {
    name: 'FrameworksPage',
    
    components: {
      PopupSpinner
    },
    
    data() {
      return {
        filterPlaceholder: 'Type here to filter frameworks', // Placeholder text for table filter box
        filterText: '',  // Text in the table filter box
        allSelected: false, // Are all of the frameworks selected?
        sortColumn: 'name',  // Column of table used for sorting the frameworks: name, country, creationTime, updatedTime, dataUploadTime
        sortReverse: false, // Sort in reverse order?
        frameworkSummaries: [], // List of summary objects for frameworks the user has
        frame_name: 'New framework', // For creating a new framework: number of populations
        num_comps: 5, // For creating a new framework: number of populations
        frameworkOptions: [],
        currentFramework: ''
      }
    },

    computed: {
      sortedFilteredFrameworkSummaries() {
        return this.applyNameFilter(this.applySorting(this.frameworkSummaries))
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
        this.getFrameworkOptions()
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

      getFrameworkOptions() {
        console.log('getFrameworkOptions() called')
        rpcservice.rpcCall('get_framework_options') // Get the current user's framework summaries from the server.
          .then(response => {
            this.frameworkOptions = response.data // Set the frameworks to what we received.
            this.currentFramework = this.frameworkOptions[0]
            console.log(this.frameworkOptions)
          })
          .catch(error => {
            status.failurePopup(this, 'Could not load framework options: ' + error.message)
          })
      },

      updateFrameworkSummaries() {
        console.log('updateFrameworkSummaries() called')
        rpcservice.rpcCall('load_current_user_framework_summaries') // Get the current user's framework summaries from the server.
        .then(response => {
          this.frameworkSummaries = response.data.frameworks // Set the frameworks to what we received.
          this.frameworkSummaries.forEach(theFrame => { // Preprocess all frameworks.
            theFrame.selected = false // Set to not selected.
            theFrame.renaming = '' // Set to not being renamed.
            theFrame.framework.creationTime = new Date(theFrame.framework.creationTime) // Extract actual Date objects from the strings.
            theFrame.framework.updatedTime = new Date(theFrame.framework.updatedTime)
          })
          console.log(this.frameworkSummaries)
        })
        .catch(error => {
          status.failurePopup(this, 'Could not load frameworks: ' + error.message)
        })
      },

      addDemoFramework() {
        console.log('addDemoFramework() called')
        this.$modal.hide('demo-framework')
        status.start(this) // Start indicating progress.
        rpcservice.rpcCall('add_demo_framework', [this.$store.state.currentUser.UID, this.currentFramework]) // Have the server create a new framework.
        .then(response => {         
          // Update the framework summaries so the new framework shows up on the list.
          this.updateFrameworkSummaries()
          
          // Indicate success.
          status.succeed(this, 'Library framework loaded')
        })
        .catch(error => {
          // Indicate failure.
          status.fail(this, 'Could not load framework')  
        })            
      },

      addDemoFrameworkModal() {
        // Open a model dialog for creating a new framework
        console.log('addDemoFrameworkModal() called');
        this.$modal.show('demo-framework');
      },

      createNewFramework() {
        console.log('createNewFramework() called')
        this.$modal.hide('create-framework')
        status.start(this) // Start indicating progress.
        rpcservice.rpcDownloadCall('create_new_framework') // Have the server create a new framework.
        .then(response => {
          status.succeed(this, '')
        })
        .catch(error => {
          status.fail(this, 'Could not download the framework: ' + error.message)
        })        
      },

      uploadFrameworkFromFile() {
        console.log('uploadFrameworkFromFile() called')
          rpcservice.rpcUploadCall('create_framework_from_file', [this.$store.state.currentUser.UID], {}, '.xlsx') // Have the server upload the framework.
          .then(response => {
            status.start(this) // Start indicating progress.
            this.updateFrameworkSummaries() // Update the framework summaries so the new framework shows up on the list.
            status.succeed(this, 'Framework uploaded')
          })
          .catch(error => {
            status.fail(this, 'Could not upload the framework: ' + error.message)
          })
          .finally(response => {
          })
      },

      frameworkIsActive(uid) {
        if (this.$store.state.activeFramework.framework === undefined) { // If the framework is undefined, it is not active.
          return false
        } else { // Otherwise, the framework is active if the UIDs match.
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
        try {
          console.log('Filtering frameworks')
          return frameworks.filter(theFramework => theFramework.framework.name.toLowerCase().indexOf(this.filterText.toLowerCase()) !== -1)
        } catch(err) {
          console.log('Filtering failed: ' + err.message)
        }
      },

      applySorting(frameworks) {
        return frameworks.slice(0).sort((frw1, frw2) =>
          {
            let sortDir = this.sortReverse ? -1: 1
            if (this.sortColumn === 'name') {
              return (frw1.framework.name > frw2.framework.name ? sortDir: -sortDir)
            }
            /*          else if (this.sortColumn === 'country') {
             return frw1.country > frw2.country ? sortDir: -sortDir
             } */
            else if (this.sortColumn === 'creationTime') {
              return frw1.framework.creationTime > frw2.framework.creationTime ? sortDir: -sortDir
            }
            else if (this.sortColumn === 'updatedTime') {
              return frw1.framework.updatedTime > frw2.framework.updatedTime ? sortDir: -sortDir
            }
          }
        )
      },

      copyFramework(uid) {
        let matchFramework = this.frameworkSummaries.find(theFrame => theFrame.framework.id === uid) // Find the framework that matches the UID passed in.
        console.log('copyFramework() called for ' + matchFramework.framework.name)
        status.start(this)
        rpcservice.rpcCall('copy_framework', [uid]) // Have the server copy the framework, giving it a new name.
        .then(response => {
          this.updateFrameworkSummaries() // Update the framework summaries so the copied program shows up on the list.
          status.succeed(this, 'Framework "'+matchFramework.framework.name+'" copied')
        })
        .catch(error => {
          status.fail(this, 'Could not copy framework:' + error.message)
        })       
      },

      renameFramework(frameworkSummary) {
        console.log('renameFramework() called for ' + frameworkSummary.framework.name)
        if (frameworkSummary.renaming === '') { // If the framework is not in a mode to be renamed, make it so.
          frameworkSummary.renaming = frameworkSummary.framework.name
        }
        else { // Otherwise (it is to be renamed)...
          let newFrameworkSummary = JSON.parse(JSON.stringify(frameworkSummary)) // Make a deep copy of the frameworkSummary object by JSON-stringifying the old object, and then parsing the result back into a new object.
          newFrameworkSummary.framework.name = frameworkSummary.renaming // Rename the framework name in the client list from what's in the textbox.
          status.start(this) // Start indicating progress.
          rpcservice.rpcCall('update_framework_from_summary', [newFrameworkSummary]) // Have the server change the name of the framework by passing in the new copy of the summary.
          .then(response => {
            this.updateFrameworkSummaries() // Update the framework summaries so the rename shows up on the list.
            frameworkSummary.renaming = '' // Turn off the renaming mode.
            status.succeed(this, '')
          })
          .catch(error => {
            status.fail(this, 'Could not rename framework:' + error.message)
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
                
        status.start(this) // Start indicating progress.
      
        // Make the server call to download the framework to a .prj file.
        rpcservice.rpcDownloadCall('download_framework', [uid])
        .then(response => {
          status.succeed(this, '')        
        })
        .catch(error => {
          status.fail(this, 'Could not rename framework:' + error.message)     
        })             
      },

      downloadDefaults(uid) {
        // Find the framework that matches the UID passed in.
        let matchFramework = this.frameworkSummaries.find(theFrame => theFrame.framework.id === uid)

        console.log('downloadDefaults() called for ' + matchFramework.framework.name)

        // Make the server call to download the framework to a .prj file.
        rpcservice.rpcDownloadCall('download_defaults', [uid])
        .catch(error => {
          status.failurePopup(this, 'Could not download defaults:' + error.message)     
        })        
      },

      // Confirmation alert
      deleteModal() {
        // Pull out the names of the frameworks that are selected.
        let selectFrameworksUIDs = this.frameworkSummaries.filter(theFrame =>
          theFrame.selected).map(theFrame => theFrame.framework.id)
          
        // Only if something is selected...
        if (selectFrameworksUIDs.length > 0) {
          // Alert object data
          var obj = {
            message: 'Are you sure you want to delete the selected frameworks?',
            useConfirmBtn: true,
            customConfirmBtnClass: 'btn __red',
            customCloseBtnClass: 'btn',
            onConfirm: this.deleteSelectedFrameworks
          }
          this.$Simplert.open(obj)
        }
      },

      deleteSelectedFrameworks() {
        // Pull out the names of the frameworks that are selected.
        let selectFrameworksUIDs = this.frameworkSummaries.filter(theFrame =>
          theFrame.selected).map(theFrame => theFrame.framework.id)

        console.log('deleteSelectedFrameworks() called for ', selectFrameworksUIDs)
              
        // Have the server delete the selected frameworks.
        if (selectFrameworksUIDs.length > 0) {
          status.start(this) // Start indicating progress.         
          
          rpcservice.rpcCall('delete_frameworks', [selectFrameworksUIDs])
          .then(response => {
            // Get the active framework ID.
/*            let activeFrameworkId = this.$store.state.activeFramework.framework.id
            if (activeFrameworkId === undefined) {
              activeFrameworkId = null
            } 
          
            // Update the framework summaries so the deletions show up on the list. 
            // Make sure it tries to set the framework that was active.
            // TODO: This will cause problems until we add a check to 
            // updateFrameworkSummaries() to make sure a framework still exists with 
            // that ID.
            this.updateFrameworkSummaries(activeFrameworkId) */
              
            this.updateFrameworkSummaries(null)
            
            status.succeed(this, '')              
          })
          .catch(error => {
            status.fail(this, 'Could not delete framework/s:' + error.message)      
          })                    
        }
      },

      downloadSelectedFrameworks() {
        // Pull out the names of the frameworks that are selected.
        let selectFrameworksUIDs = this.frameworkSummaries.filter(theFrame =>
          theFrame.selected).map(theFrame => theFrame.framework.id)

        console.log('deleteSelectedFrameworks() called for ', selectFrameworksUIDs)
                 
        // Have the server download the selected frameworks.
        if (selectFrameworksUIDs.length > 0) {
          status.start(this) // Start indicating progress.
          
          rpcservice.rpcDownloadCall('load_zip_of_frw_files', [selectFrameworksUIDs])
          .then(response => {
            status.succeed(this, '')         
          })
          .catch(error => {
            status.fail(this, 'Could not download framework/s:' + error.message) 
          })        
        }           
      }
    }
  }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang="scss" scoped>
</style>
