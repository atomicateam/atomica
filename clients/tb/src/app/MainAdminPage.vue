<!--
Admin page

Last update: 2018-05-28
-->

<template>
  <div class="SitePage">
    <h2>Users</h2>
    <table v-if="usersList[0] != undefined">
      <tr>
        <th>Username</th>
        <th>Display name</th>
        <th>Email</th>
        <th>Account active?</th>
        <th>Admin?</th>
        <th>Actions</th>
      </tr>
      <tr v-for="userobj in usersList">
        <td>{{ userobj.user.username }}</td>
        <td>{{ userobj.user.displayname }}</td>
        <td>{{ userobj.user.email }}</td>
        <td>{{ userobj.user.accountactive }}</td>
        <td>{{ userobj.user.admin }}</td>
        <td>
          <button @click="activateAccount(userobj.user.username)">Activate Account</button>
          <button @click="deactivateAccount(userobj.user.username)">Deactivate Account</button>
          <button @click="grantAdmin(userobj.user.username)">Grant Admin</button>
          <button @click="revokeAdmin(userobj.user.username)">Revoke Admin</button>
          <button @click="resetPassword(userobj.user.username)">Reset Password</button>
          <button @click="deleteUser(userobj.user.username)">Delete Account</button>
        </td>
      </tr>
    </table>

    <p v-if="adminResult != ''">{{ adminResult }}</p>
  </div>
</template>

<script>
import rpcs from '@/services/rpc-service'
import userservice from '@/services/user-service'
import router from '@/router'

export default {
  name: 'MainAdminPage',

  data () {
    return {
      usersList: [],
      adminResult: ''
    }
  },

  created () {
    this.getUsersInfo()
  },

  methods: {
    getUsersInfo () {
      userservice.getAllUsersInfo()
      .then(response => {
        this.usersList = response.data
      })
      .catch(error => {
        // Give result message.
        this.adminResult = 'Could not load users from server.'
      })
    },

    activateAccount (username) {
      userservice.activateUserAccount(username)
      .then(response => {
        // If the response was successful...
        if (response.data == 'success')
          // Give result message.
          this.adminResult = 'User account activated.'
        // Otherwise (failure)
        else
          // Give result message.
          this.adminResult = 'Account activation not successful.'

        // Get the users info again.
        this.getUsersInfo()
      })
      .catch(error => {
        // Give result message.
        this.adminResult = 'Account activation not successful.'
      })
    },

    deactivateAccount (username) {
      userservice.deactivateUserAccount(username)
      .then(response => {
        // If the response was successful...
        if (response.data == 'success')
          // Give result message.
          this.adminResult = 'User account deactivated.'
        // Otherwise (failure)
        else
          // Give result message.
          this.adminResult = 'Account deactivation not successful.'

        // Get the users info again.
        this.getUsersInfo()
      })
      .catch(error => {
        // Give result message.
        this.adminResult = 'Account deactivation not successful.'
      })
    },

    grantAdmin (username) {
      userservice.grantUserAdminRights(username)
      .then(response => {
        // If the response was successful...
        if (response.data == 'success')
          // Give result message.
          this.adminResult = 'Admin access granted.'
        // Otherwise (failure)
        else
          // Give result message.
          this.adminResult = 'Admin granting not successful.'

        // Get the users info again.
        this.getUsersInfo()
      })
      .catch(error => {
        // Give result message.
        this.adminResult = 'Admin granting not successful.'
      })
    },

    revokeAdmin (username) {
      userservice.revokeUserAdminRights(username)
      .then(response => {
        // If the response was successful...
        if (response.data == 'success')
          // Give result message.
          this.adminResult = 'Admin access revoked.'
        // Otherwise (failure)
        else
          // Give result message.
          this.adminResult = 'Admin revocation not successful.'

        // Get the users info again.
        this.getUsersInfo()
      })
      .catch(error => {
        // Give result message.
        this.adminResult = 'Admin revocation not successful.'
      })
    },

    resetPassword (username) {
      userservice.resetUserPassword(username)
      .then(response => {
        // If the response was successful...
        if (response.data == 'success')
          // Give result message.
          this.adminResult = 'Password reset.'
        // Otherwise (failure)
        else
          // Give result message.
          this.adminResult = 'Password reset not successful.'

        // Get the users info again.
        this.getUsersInfo()
      })
      .catch(error => {
        // Give result message.
        this.adminResult = 'Password reset not successful.'
      })
    },

    deleteUser (username) {
      userservice.deleteUser(username)
      .then(response => {
        // Give result message.
        this.adminResult = 'User deleted.'

        // Get the users info again.
        this.getUsersInfo()
      })
      .catch(error => {
        // Give result message.
        this.adminResult = 'Deletion not successful.'
      })
    }

  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
