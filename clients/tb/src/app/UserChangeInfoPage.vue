<!--
Change account info

Last update: 2018-08-18
-->

<template>
  <div>

    <form name="ChangeUserInfo" @submit.prevent="tryChangeInfo" style="max-width: 500px; min-width: 100px; margin: 0 0">

      <div class="divTable">
        <div class="divTableBody">
          <div class="divTableRow" style="line-height:40px">
            <div class="divRowLabel">Username </div>
            <div class="divRowContent section form-input-validate" style="min-width:100%; vertical-align:middle">
              <input class="txbox __l"
                     type="text"
                     name="changeusername"
                     required="required"
                     v-model='changeUserName'/>
            </div>
          </div>
          <div class="divTableRow" style="line-height:40px">
            <div class="divRowLabel">Display&nbsp;name </div>
            <div class="divRowContent section form-input-validate" style="min-width:100%; vertical-align:middle">
              <input class="txbox __l"
                     type="text"
                     name="changedisplayname"
                     v-model='changeDisplayName'/>
            </div>
          </div>
          <div class="divTableRow" style="line-height:40px">
            <div class="divRowLabel">Email </div>
            <div class="divRowContent section form-input-validate" style="min-width:100%; vertical-align:middle">
              <input class="txbox __l"
                     type="text"
                     name="changedemail"
                     v-model='changeEmail'/>
            </div>
          </div>
        </div>
        <div class="divTableRow" style="line-height:40px">
          <div class="divRowLabel">Enter&nbsp;password</div>
          <div class="divRowContent section form-input-validate" style="min-width:100%; vertical-align:middle">
            <input class="txbox __l"
                   type="password"
                   name="changepassword"
                   required="required"
                   v-model='changePassword'/>
          </div>
        </div>
      </div>

      <button type="submit" class="section btn __l __block">Update</button>
      <br/>
      <p v-if="changeResult != ''">{{ changeResult }}</p>
    </form>

  </div>
</template>

<script>
  import userservice from '@/js/user-service'
  import status from '@/js/status-service'
  import router from '@/router'

  export default {
    name: 'UserChangeInfoPage',

    data () {
      return {
        changeUserName:    this.$store.state.currentUser.username,
        changeDisplayName: this.$store.state.currentUser.displayname,
        changeEmail:       this.$store.state.currentUser.email,
        changePassword:    '',
        changeResult:      ''
      }
    },

    methods: {
      tryChangeInfo () {
        userservice.changeUserInfo(this.changeUserName, this.changePassword,
          this.changeDisplayName, this.changeEmail)
          .then(response => {
            if (response.data === 'success') {
              status.succeed(this, 'User info updated') // Set a success result to show.
              userservice.getCurrentUserInfo() // Read in the full current user information.
                .then(response2 => {
                  this.$store.commit('newUser', response2.data.user) // Set the username to what the server indicates.
                  router.push('/') // Navigate automatically to the home page.
                })
                .catch(error => {
                  this.$store.commit('newUser', {}) // Set the username to {}.  An error probably means the user is not logged in.
                })
            } else {
              this.changeResult = response.data
            }
          })
          .catch(error => {
            status.fail(this, 'Failed to update user info, please check password and try again', error)
          })
      }
    }
  }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
