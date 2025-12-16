const CACHE_NAME = 'princesa-app-v1.2.1';
const urlsToCache = [
    '/',
    '/login',
    '/dashboard', 
    '/tasks',
    '/routines',
    '/static/css/princess-style.css',
    '/static/css/login.css',
    '/static/css/dashboard.css',
    '/static/css/tasks.css',
    '/static/css/routines.css',
    '/static/css/animations.css',
    '/static/js/app.js',
    '/static/js/notifications.js',
    '/static/js/dashboard.js',
    '/static/js/tasks.js',
    '/static/js/routines.js',
    '/static/icons/icon-32x32.png',
    '/static/icons/icon-144x144.png',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png',
    '/static/manifest.json'
];

// URLs externas que não devem ser cacheadas
const externalResources = [
    'https://cdn.jsdelivr.net',
    'https://cdnjs.cloudflare.com',
    'https://fonts.googleapis.com',
    'https://fonts.gstatic.com'
];

// Instalar Service Worker
self.addEventListener('install', function(event) {
    console.log('🌸 Service Worker: Instalando...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function(cache) {
                console.log('🌸 Service Worker: Cache criado');
                return cache.addAll(urlsToCache);
            })
            .catch(function(error) {
                console.log('🌸 Service Worker: Erro no cache:', error);
            })
    );
});

// Ativar Service Worker
self.addEventListener('activate', function(event) {
    console.log('🌸 Service Worker: Ativando...');
    event.waitUntil(
        caches.keys().then(function(cacheNames) {
            return Promise.all(
                cacheNames.map(function(cacheName) {
                    if (cacheName !== CACHE_NAME) {
                        console.log('🌸 Service Worker: Removendo cache antigo:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// Interceptar requisições
self.addEventListener('fetch', function(event) {
    const requestUrl = new URL(event.request.url);
    
    // Pular recursos de extensões do browser
    if (requestUrl.protocol === 'chrome-extension:' || requestUrl.protocol === 'moz-extension:') {
        return;
    }
    
    // Estratégia diferente para recursos externos
    const isExternal = externalResources.some(domain => event.request.url.includes(domain));
    
    if (isExternal) {
        // Para recursos externos: network first, sem cache
        event.respondWith(
            fetch(event.request).catch(function() {
                console.log('🌸 Recurso externo falhou:', event.request.url);
                return new Response('Resource unavailable', { status: 503 });
            })
        );
        return;
    }
    
    // Para recursos internos: cache first
    event.respondWith(
        caches.match(event.request)
            .then(function(response) {
                // Se encontrou no cache, retorna
                if (response) {
                    return response;
                }
                
                // Se não encontrou, faz requisição à rede
                return fetch(event.request).then(function(response) {
                    // Verifica se a resposta é válida para cache
                    if (!response || response.status !== 200 || response.type !== 'basic') {
                        return response;
                    }

                    // Clona a resposta para o cache apenas se for recurso interno
                    var responseToCache = response.clone();
                    caches.open(CACHE_NAME).then(function(cache) {
                        cache.put(event.request, responseToCache);
                    });

                    return response;
                }).catch(function() {
                    // Se offline e não tem no cache, mostra página offline
                    if (event.request.destination === 'document') {
                        return caches.match('/login');
                    }
                });
            })
    );
});

// Notificações Push (futura implementação)
self.addEventListener('push', function(event) {
    console.log('🌸 Push recebido:', event);
    
    const options = {
        body: event.data ? event.data.text() : 'Nova tarefa adicionada!',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/icon-72x72.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: '2'
        },
        actions: [
            {
                action: 'explore',
                title: 'Ver Detalhes',
                icon: '/static/icons/checkmark.png'
            },
            {
                action: 'close', 
                title: 'Fechar',
                icon: '/static/icons/close.png'
            }
        ]
    };

    event.waitUntil(
        self.registration.showNotification('Princesa App 👑', options)
    );
});

// Clique na notificação
self.addEventListener('notificationclick', function(event) {
    console.log('🌸 Notificação clicada:', event.notification.tag);
    
    event.notification.close();

    if (event.action === 'explore') {
        event.waitUntil(clients.openWindow('/dashboard'));
    } else if (event.action === 'close') {
        console.log('🌸 Notificação fechada');
    } else {
        event.waitUntil(clients.openWindow('/'));
    }
});

// Background sync (para quando voltar online)
self.addEventListener('sync', function(event) {
    console.log('🌸 Background sync:', event.tag);
    
    if (event.tag === 'background-sync') {
        event.waitUntil(syncTasks());
    }
});

async function syncTasks() {
    // Sincronizar tarefas pendentes quando voltar online
    console.log('🌸 Sincronizando tarefas...');
    
    try {
        const response = await fetch('/api/sync-tasks', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (response.ok) {
            console.log('🌸 Tarefas sincronizadas com sucesso!');
        }
    } catch (error) {
        console.log('🌸 Erro na sincronização:', error);
    }
}