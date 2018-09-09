<!--
Change the user's password

Last update: 2018-08-26
-->

<template>
  <div>

    <form name="ChangePasswordForm" @submit.prevent="tryChangePassword" style="max-width: 300px; min-width: 100px; margin: 0 0">

      <div class="section form-input-validate">
        <input class="txbox __l"
               type="password"
               name="oldpassword"
               placeholder="Reenter old password"
               required="required"
               v-model='oldPassword'/>
      </div>

      <div class="section form-input-validate">
        <input class="txbox __l"
               type="password"
               name="password"
               placeholder="Enter new password"
               required="required"
               v-model='newPassword'/>
      </div>

      <button type="submit" class="section btn __l __block">Update</button>

      <br/>

      <p v-if="changeResult != ''">{{ changeResult }}</p>
    </form>
  </div>
</template>

<script>
import userservice from '@/js/user-service'
import router from '@/router'

export default {
  name: 'ChangePasswordPage',

  data () {
    return {
      oldPassword: '',
      newPassword: '',
      changeResult: ''
    }
  },

  methods: {
    tryChangePassword () {
      userservice.changeUserPassword(this.oldPassword, this.newPassword)
      .then(response => {
        if (response.data == 'success') {
          // Set a success result to show.
          this.$notifications.notify({
            message: 'Password updated',
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
            message: 'Password update failed',
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
