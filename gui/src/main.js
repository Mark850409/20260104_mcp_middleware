import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './assets/design-system.css'

const app = createApp(App)

// 註冊 click-outside 指令
app.directive('click-outside', {
    mounted(el, binding) {
        el.clickOutsideEvent = function (event) {
            if (!(el === event.target || el.contains(event.target))) {
                binding.value(event)
            }
        }
        document.addEventListener('click', el.clickOutsideEvent)
    },
    unmounted(el) {
        document.removeEventListener('click', el.clickOutsideEvent)
    }
})

app.use(router)
app.mount('#app')

