const CACHE_NAME = 'princesa-app-v1.2.0';
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
    '/static/js/princess-app.js',
    '/static/js/dashboard.js',
    '/static/js/tasks.js',
    '/static/js/routines.js',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js'
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
    event.respondWith(
        caches.match(event.request)
            .then(function(response) {
                // Se encontrou no cache, retorna
                if (response) {
                    return response;
                }
                
                // Se não encontrou, faz requisição à rede
                return fetch(event.request).then(function(response) {
                    // Verifica se a resposta é válida
                    if (!response || response.status !== 200 || response.type !== 'basic') {
                        return response;
                    }

                    // Clona a resposta para o cache
                    var responseToCache = response.clone();
                    caches.open(CACHE_NAME).then(function(cache) {
                        cache.put(event.request, responseToCache);
                    });

                    return response;
                }).catch(function() {
                    // Se offline e não tem no cache, mostra página offline
                    if (event.request.destination === 'document') {
                        return caches.match('/offline');
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