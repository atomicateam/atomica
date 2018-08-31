// index.js -- vue-router path configuration code
//
// Last update: 2018-08-30

// Import main things
import Vue from 'vue'
import Router from 'vue-router'
import DashboardLayout from '@/app/DashboardLayout.vue'

// App views
import NotFound from '@/app/NotFoundPage.vue'
import ProjectsPage from '@/app/ProjectsPage'
import CalibrationPage from '@/app/CalibrationPage'
import ScenariosPage from '@/app/ScenariosPage'
import OptimizationsPage from '@/app/OptimizationsPage'
import LoginPage from '@/app/LoginPage'
import MainAdminPage from '@/app/MainAdminPage'
import RegisterPage from '@/app/RegisterPage'
import UserChangeInfoPage from '@/app/UserChangeInfoPage'
import ChangePasswordPage from '@/app/ChangePasswordPage'
import Help from '@/app/Help'
import Contact from '@/app/Contact'
import About from '@/app/About'


Vue.use(Router);

export default new Router({
  routes: [
    {
      path: '/register',
      name: 'Registration',
      component: RegisterPage
    },
    {
      path: '/login',
      name: 'Login',
      component: LoginPage
    },
    {
      path: '/',
      component: DashboardLayout,
      redirect: '/projects',
      children: [
        {
          path: 'projects',
          name: 'Manage projects',
          component: ProjectsPage
        },
        {
          path: 'calibration',
          name: 'Calibration',
          component: CalibrationPage
        },
        {
          path: 'scenarios',
          name: 'Create scenarios',
          component: ScenariosPage
        },
        {
          path: 'optimizations',
          name: 'Create optimizations',
          component: OptimizationsPage
        },
        {
          path: 'mainadmin',
          name: 'Admin',
          component: MainAdminPage
        },
        {
          path: 'changeinfo',
          name: 'Edit account',
          component: UserChangeInfoPage
        },
        {
          path: 'changepassword',
          name: 'Change password',
          component: ChangePasswordPage
        },
        {
          path: 'help',
          name: 'Help',
          component: Help
        },
        {
          path: 'contact',
          name: 'Contact',
          component: Contact
        },
        {
          path: 'about',
          name: 'About',
          component: About
        },
      ]
    },
    { path: '*', component: NotFound }
  ]
})
