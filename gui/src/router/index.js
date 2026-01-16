/**
 * Vue Router 配置
 * 定義路由並實作認證守衛
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../composables/useAuth'

// 路由定義
const routes = [
    {
        path: '/login',
        name: 'Login',
        component: () => import('../views/Login.vue'),
        meta: { requiresAuth: false, title: '登入' }
    },
    {
        path: '/register',
        name: 'Register',
        component: () => import('../views/Register.vue'),
        meta: { requiresAuth: false, title: '註冊' }
    },
    {
        path: '/',
        name: 'Home',
        component: () => import('../layouts/MainLayout.vue'),
        meta: { requiresAuth: true, title: 'MCP Platform' },
        redirect: '/chatbot',
        children: [
            {
                path: '/chatbot',
                name: 'Chatbot',
                component: () => import('../components/Chatbot.vue'),
                meta: { requiresAuth: true, pageCode: 'chatbot' }
            },
            {
                path: '/agents',
                name: 'Agents',
                component: () => import('../components/AgentManagement.vue'),
                meta: { requiresAuth: true, pageCode: 'agents' }
            },
            {
                path: '/mcp',
                name: 'MCP',
                component: () => import('../components/MCPManagement.vue'),
                meta: { requiresAuth: true, pageCode: 'mcp' }
            },
            {
                path: '/linebot',
                name: 'LineBot',
                component: () => import('../components/LineBotManagement.vue'),
                meta: { requiresAuth: true, pageCode: 'linebot' }
            },
            {
                path: '/prompts',
                name: 'Prompts',
                component: () => import('../components/PromptManagement.vue'),
                meta: { requiresAuth: true, pageCode: 'prompts' }
            },
            {
                path: '/rag',
                name: 'RAG',
                component: () => import('../components/KnowledgeBaseManagement.vue'),
                meta: { requiresAuth: true, pageCode: 'rag' }
            },
            {
                path: '/users',
                name: 'Users',
                component: () => import('../components/UserManagement.vue'),
                meta: { requiresAuth: true, pageCode: 'users' }
            },
            {
                path: '/roles',
                name: 'Roles',
                component: () => import('../components/RoleManagement.vue'),
                meta: { requiresAuth: true, pageCode: 'roles' }
            }
        ]
    }
]

// 建立 Router 實例
const router = createRouter({
    history: createWebHistory(),
    routes
})

// 全域路由守衛
router.beforeEach(async (to, from, next) => {
    const { isAuthenticated, fetchCurrentUser, hasPagePermission, hasRole } = useAuth()

    // 設定頁面標題
    document.title = to.meta.title || 'MCP Platform'

    // 檢查是否需要認證
    if (to.meta.requiresAuth) {
        // 如果未登入,嘗試從 Token 恢復登入狀態
        if (!isAuthenticated.value) {
            const user = await fetchCurrentUser()

            if (!user) {
                // Token 無效或不存在,重導向到登入頁
                next({
                    path: '/login',
                    query: { redirect: to.fullPath }
                })
                return
            }
        }

        // 檢查角色權限
        if (to.meta.requiresRole) {
            if (!hasRole(to.meta.requiresRole)) {
                console.error(`需要角色: ${to.meta.requiresRole}`)
                next({ path: '/' })
                return
            }
        }

        // 檢查頁面權限
        if (to.meta.pageCode) {
            if (!hasPagePermission(to.meta.pageCode)) {
                console.error(`沒有訪問 ${to.meta.pageCode} 頁面的權限`)
                next({ path: '/' })
                return
            }
        }
    } else {
        // 如果已登入且訪問登入/註冊頁,重導向到首頁
        if (isAuthenticated.value && (to.path === '/login' || to.path === '/register')) {
            next({ path: '/' })
            return
        }
    }

    next()
})

export default router
