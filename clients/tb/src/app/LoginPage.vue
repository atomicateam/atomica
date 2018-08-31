<!--
Login page

Last update: 2018-08-30
-->

<template>
  <div style="background-color:#f8f8f4; position:fixed; min-height:100%; min-width:100%; padding:0 0 0 0" v-model="getVersionInfo"> <!-- Should match _variables.scss:$bg-nude -->
    <div style="background-color:#0c2544; position:absolute; height:100%; width:260px">
      <div class="logo">
        <div class="simple-text" style="font-size:20px; color:#fff; font-weight:bold; padding:20px">
          <span style="padding-left:10px">
            <a href="http://ocds.co" target="_blank">
              <img src="static/img/optima-inverted-logo-tb.png" width="160px" vertical-align="middle" alt>
            </a>
          </span>
          <br/><br/>
          <div style="font-size:14px; font-weight:normal">
            Version {{ version }} ({{ date }})
          </div>
        </div>
      </div>
    </div>
    <div style="margin-right:-260px">
      <form name="LogInForm" @submit.prevent="tryLogin" style="max-width: 500px; min-width: 100px; margin: 0 auto">

        <div class="modal-body">
          <h2>Login</h2>

          <div class="section" v-if="loginResult != ''">{{ loginResult }}</div>

          <div class="section form-input-validate">
            <input class="txbox __l"
                   type="text"
                   name="username"
                   placeholder="User name"
                   required="required"
                   v-model='loginUserName'/>
          </div>

          <div class="section form-input-validate">
            <input class="txbox __l"
                   type="password"
                   name="password"
                   placeholder="Password"
                   required="required"
                   v-model='loginPassword'/>
          </div>

          <button type="submit" class="section btn __l __block">Login</button>

          <div class="section">
            New user?
            <router-link to="/register">
              Register here
            </router-link>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
  import rpcs from '@/services/rpc-service'
  import userservice from '@/services/user-service'
  import router from '@/router'

  export default {
    name: 'LoginPage',

    data () {
      return {
        loginUserName: '',
        loginPassword: '',
        loginResult: '',
        version: '',
        date: '',
      }
    },

    computed: {
      getVersionInfo() {
        rpcs.rpc('get_version_info')
        .then(response => {
          this.version = response.data['version'];
          this.date = response.data['date'];
        })
      },
    },

    methods: {
      tryLogin () {
        userservice.loginCall(this.loginUserName, this.loginPassword)
        .then(response => {
          if (response.data == 'success') {
            // Set a success result to show.
            this.loginResult = 'Logging in...'

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
            this.loginResult = 'Login failed: username or password incorrect or account not activated.'
          }
        })
        .catch(error => {
          console.log('Login failed: ' + error.message)
          this.loginResult = "We're sorry, it seems we're having trouble communicating with the server.  Please contact support or try again later."
        })
      }
    }
  }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
