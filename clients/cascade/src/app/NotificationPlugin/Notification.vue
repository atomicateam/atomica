<template>
  <div
    data-notify="container"
    class="alert open alert-with-icon"
    role="alert"
    :class="[verticalAlign, horizontalAlign, alertType]"
    :style="customPosition"
    data-notify-position="top-center">

    <!--<div class="divTable">-->
      <!--<div class="divRow">-->
        <!--<div class="divRowContent alert-icon" data-notify="message" :class="icon" style="font-size:20px"></div> &lt;!&ndash; Icon &ndash;&gt;-->
        <!--<div class="divRowContent" data-notify="message" v-html="message"></div>&lt;!&ndash; Message &ndash;&gt;-->
        <!--<div class="divRowContent"> &lt;!&ndash; Close button &ndash;&gt;-->
          <!--<button-->
            <!--type="button"-->
            <!--aria-hidden="true"-->
            <!--class="close"-->
            <!--data-notify="dismiss"-->
            <!--@click="close">×-->
          <!--</button>-->
        <!--</div>-->
      <!--</div>-->
    <!--</div>-->

    <div id = "flex">
      <div><span class="alert-icon" data-notify="message" :class="icon" style="font-size:20px"></span></div> <!-- Icon -->
      <div style="max-width:400px;"><span data-notify="message" v-html="message"></span></div><!-- Message -->
      <div> <!-- Close button -->
        <button
          type="button"
          aria-hidden="true"
          class="close"
          data-notify="dismiss"
          @click="close">×
        </button>
      </div>
    </div>

  </div>
</template>
<script>
  export default {
    name: 'notification',
    props: {
      message: String,
      icon: {
        type: String,
        default: 'ti-info-alt'
      },
      verticalAlign: {
        type: String,
        default: 'top'
      },
      horizontalAlign: {
        type: String,
        default: 'center'
      },
      type: {
        type: String,
        default: 'info'
      },
      timeout: {
        type: Number,
        default: 2000
      },
      timestamp: {
        type: Date,
        default: () => new Date()
      },      
    },
    data () {
      return {}
    },
    computed: {
      hasIcon () {
        return this.icon && this.icon.length > 0
      },
      alertType () {
        return `alert-${this.type}`
      },
      customPosition () {
        let initialMargin = 20
        let alertHeight = 60
        let sameAlertsCount = this.$notifications.state.filter((alert) => {
          return alert.horizontalAlign === this.horizontalAlign && alert.verticalAlign === this.verticalAlign
        }).length
        let pixels = (sameAlertsCount - 1) * alertHeight + initialMargin
        let styles = {}
        if (this.verticalAlign === 'top') {
          styles.top = `${pixels}px`
        } else {
          styles.bottom = `${pixels}px`
        }
        return styles
      }
    },
    methods: {
      close () {
        console.log('Dialog closing: ', this.timestamp)
        this.$parent.$emit('on-close', this.timestamp)  
      }
    },
    mounted () {
      console.log('Dialog opening? ', this.timestamp)
      if (this.timeout) {
        setTimeout(this.close, this.timeout)
      }
    }
  }

</script>
<style lang="scss" scoped>
  @import "../../sass/project/variables";

  .fade-enter-active,
  .fade-leave-active {
    transition: opacity .3s
  }

  .fade-enter,
  .fade-leave-to
  /* .fade-leave-active in <2.1.8 */

  {
    opacity: 0
  }

  .alert {
    border: 0;
    border-radius: 0;
    color: #FFFFFF;
    padding: 20px 15px;
    font-size: 14px;
    z-index: 100;
    display: inline-block;
    position: fixed;
    transition: all 0.5s ease-in-out;

    &.center {
      left: 0px;
      right: 0px;
      margin: 0 auto;
    }
    &.left {
      left: 20px;
    }
    &.right {
      right: 20px;
    }
    .container & {
      border-radius: 4px;
    }
    .navbar & {
      border-radius: 0;
      left: 0;
      position: absolute;
      right: 0;
      top: 85px;
      width: 100%;
      z-index: 3;
    }
    .navbar:not(.navbar-transparent) & {
      top: 70px;
    }

    .alert-icon {
      font-size: 30px;
      margin-right: 5px;
    }

    .close~span {
      display: inline-block;
      max-width: 89%;
    }

    &[data-notify="container"] {
      /*max-width: 400px;*/
      /*padding: 20px 10px 10px 20px; // CK: This actually affects the padding!*/
      border-radius: $border-radius-base;
    }

    &.alert-with-icon {
      /*padding-left: 15px; // CK: actual left padding*/
    }
  }

  .alert-info {
    background-color: $bg-info;
    color: $info-states-color;
  }

  .alert-success {
    background-color: $bg-success;
    color: $success-states-color;
  }

  .alert-warning {
    background-color: $bg-warning;
    color: $warning-states-color;
  }

  .alert-danger {
    background-color: $bg-danger;
    color: $danger-states-color;
  }

  #flex {display: flex; justify-content: space-between;}
  #flex div { padding: 4px; }

</style>
