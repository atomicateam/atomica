import rpcs from '@/js/rpc-service'
import store from '@/store'
import router from '@/router'
var state = {
  currentUser: {}
};
var CryptoApi = require('crypto-api')

// Lower level user functions that call RPC service functions

// loginCall() -- Call rpc() for performing a login.
function loginCall(username, password) {
  // Get a hex version of a hashed password using the SHA224 algorithm.
  var hashPassword = CryptoApi.hash('sha224', password).stringify('hex')
  
  // Make the actual RPC call.
  return rpcs.rpc('user_login', [username, hashPassword])
}

// logoutCall() -- Call rpc() for performing a logout.
function logoutCall() {
  // Make the actual RPC call.
  return rpcs.rpc('user_logout')
}

// getCurrentUserInfo() -- Call rpc() for reading the currently
// logged in user.
function getCurrentUserInfo() {
  // Make the actual RPC call.
  return rpcs.rpc('get_current_user_info')  
}

// getAllUsersInfo() -- Call rpc() for reading all of the users.
function getAllUsersInfo() {
  // Make the actual RPC call.
  return rpcs.rpc('get_all_users')   
}

// registerUser() -- Call rpc() for registering a new user.
function registerUser(username, password, displayname, email) {
  // Get a hex version of a hashed password using the SHA224 algorithm.
  var hashPassword = CryptoApi.hash('sha224', password).stringify('hex')

  // Make the actual RPC call.
  return rpcs.rpc('user_register', [username, hashPassword, displayname, email]) 
}

// changeUserInfo() -- Call rpc() for changing a user's info.
function changeUserInfo(username, password, displayname, email) {
  // Get a hex version of a hashed password using the SHA224 algorithm.
  var hashPassword = CryptoApi.hash('sha224', password).stringify('hex')
  
  // Make the actual RPC call.
  return rpcs.rpc('user_change_info', [username, hashPassword, displayname, email])   
}

// changeUserPassword() -- Call rpc() for changing a user's password.
function changeUserPassword(oldpassword, newpassword) {
  // Get a hex version of the hashed passwords using the SHA224 algorithm.
  var hashOldPassword = CryptoApi.hash('sha224', oldpassword).stringify('hex')
  var hashNewPassword = CryptoApi.hash('sha224', newpassword).stringify('hex')
  
  // Make the actual RPC call.
  return rpcs.rpc('user_change_password', [hashOldPassword, hashNewPassword])   
}

// adminGetUserInfo() -- Call rpc() for getting user information at the admin level.
function adminGetUserInfo(username) {
  // Make the actual RPC call.
  return rpcs.rpc('admin_get_user_info', [username])  
}

// deleteUser() -- Call rpc() for deleting a user.
function deleteUser(username) {
  // Make the actual RPC call.
  return rpcs.rpc('admin_delete_user', [username])   
}

// activateUserAccount() -- Call rpc() for activating a user account.
function activateUserAccount(username) {
  // Make the actual RPC call.
  return rpcs.rpc('admin_activate_account', [username])   
}

// deactivateUserAccount() -- Call rpc() for deactivating a user account.
function deactivateUserAccount(username) {
  // Make the actual RPC call.
  return rpcs.rpc('admin_deactivate_account', [username])   
}

// grantUserAdminRights() -- Call rpc() for granting a user admin rights.
function grantUserAdminRights(username) {
  // Make the actual RPC call.
  return rpcs.rpc('admin_grant_admin', [username])   
}

// revokeUserAdminRights() -- Call rpc() for revoking user admin rights.
function revokeUserAdminRights(username) {
  // Make the actual RPC call.
  return rpcs.rpc('admin_revoke_admin', [username])   
}

// resetUserPassword() -- Call rpc() for resetting a user's password.
function resetUserPassword(username) {
  // Make the actual RPC call.
  return rpcs.rpc('admin_reset_password', [username])   
}

// Higher level user functions that call the lower level ones above

function getUserInfo() {
  // Do the actual RPC call.
  getCurrentUserInfo()
  .then(response => {
    // Set the username to what the server indicates.
    store.commit('newUser', response.data.user)
  })
  .catch(error => {
    // Set the username to {}.  An error probably means the
    // user is not logged in.
    store.commit('newUser', {})
  })
}

function currentUser() {
    return store.state.currentUser
}

function checkLoggedIn() {
  if (this.currentUser.displayname == undefined)
    return false
  else
    return true
}

function checkAdminLoggedIn() {
  console.log(this)
  if (this.checkLoggedIn()) {
    return this.currentUser.admin
  }
}

function logOut() {
  // Do the actual logout RPC.
  logoutCall()
  .then(response => {
    // Update the user info.
    getUserInfo()

    // Clear out the active project.
    store.commit('newActiveProject', {})

    // Navigate to the login page automatically.
    router.push('/login')
  })
}

export default {
  loginCall,
  logoutCall,
  getCurrentUserInfo,
  getAllUsersInfo,
  registerUser,
  changeUserInfo,
  changeUserPassword,
  adminGetUserInfo,
  deleteUser,
  activateUserAccount,
  deactivateUserAccount,
  grantUserAdminRights,
  revokeUserAdminRights,
  resetUserPassword,
  getUserInfo, 
  currentUser, 
  checkLoggedIn, 
  checkAdminLoggedIn,
  logOut
}