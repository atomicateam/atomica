<!--
Change account info

Last update: 2018-05-28
-->

<template>
  <div class="SitePage">

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
import rpcs from '@/services/rpc-service'
import userservice from '@/services/user-service'
import router from '@/router'

export default {
  name: 'UserChangeInfoPage',

  data () {
    return {
      changeUserName: this.$store.state.currentUser.username,
      changeDisplayName: this.$store.state.currentUser.displayname,
      changeEmail: this.$store.state.currentUser.email,
      changePassword: '',
      changeResult: ''
    }
  },

  methods: {
    tryChangeInfo () {
      userservice.changeUserInfo(this.changeUserName, this.changePassword, 
        this.changeDisplayName, this.changeEmail)
      .then(response => {
        if (response.data == 'success') {
          // Set a success result to show.
          this.$notifications.notify({
            message: 'User info updated',
            icon: 'ti-check',
            type: 'success',
            verticalAlign: 'top',
            horizontalAlign: 'center',
          });

          // Read in the full current user information.
          userservice.getCurrentUserInfo()
          .then(response2 => {
            // Set the username to what the server indicates.
            this.$store.commit('newUser', response2.data.user)

            // Navigate automatically to the home page.
            router.push('/')
          })
          .catch(error => {
            // Set the username to {}.  An error probably means the
            // user is not logged in.
            this.$store.commit('newUser', {})
          })
        } else {
          // Set a failure result to show.
          this.$notifications.notify({
            message: 'Failed to update user info, please check password and try again',
            icon: 'ti-face-sad',
            type: 'danger',
            verticalAlign: 'top',
            horizontalAlign: 'center',
          });
        }
      })
      .catch(error => {
        this.changeResult = 'Server error.  Please try again later.'
      })
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
