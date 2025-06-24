/* ------------------------------------------------------------------
   Push-subscription helper with Brave support
   ------------------------------------------------------------------
   – Detects Brave and, if its Google-push flag is OFF, shows a friendly
     message *when the user actually clicks Subscribe* and the browser
     throws AbortError.
   ------------------------------------------------------------------ */

/* ---------- 1.  Brave detection helper --------------------------- */
 function braveNeedsPushFlag () {                         // ★ ADDED ★
  const isBrave = navigator.brave && ( navigator.brave.isBrave());
  return isBrave;
}
/* ----------------------------------------------------------------- */

var isPushEnabled = false,
    registration,
    subBtn;

window.addEventListener('load', function () {
  subBtn = document.getElementById('webpush-subscribe-button');
  subBtn.textContent = gettext('Subscribe to Push Messaging');

  subBtn.addEventListener('click', function () {
    subBtn.disabled = true;
    if (isPushEnabled) {
      return unsubscribe(registration);
    }
    return subscribe(registration);
  });

  if ('serviceWorker' in navigator) {
    const serviceWorker = document
      .querySelector('meta[name="service-worker-js"]').content;
    navigator.serviceWorker.register(serviceWorker).then(function (reg) {
      registration = reg;
      initialiseState(reg);
    });
  } else {
    showMessage(gettext('Service workers are not supported in your browser.'));
  }

  function initialiseState (reg) {
    if (!reg.showNotification) {
      showMessage(gettext('Showing notifications is not supported in your browser.'));
      return;
    }

    if (Notification.permission === 'denied') {
      subBtn.disabled = false;
      showMessage(gettext('Push notifications are blocked by your browser.'));
      return;
    }

    if (!('PushManager' in window)) {
      subBtn.disabled = false;
      showMessage(gettext('Push notifications are not available in your browser.'));
      return;
    }

    reg.pushManager.getSubscription().then(function (subscription) {
      if (subscription) {
        postSubscribeObj('subscribe', subscription, function (response) {
          if (response.status === 201) {
            subBtn.textContent = gettext('Unsubscribe from Push Messaging');
            subBtn.disabled = false;
            isPushEnabled = true;
            showMessage(gettext('Successfully subscribed to push notifications.'));
          }
        });
      }
    });
  }
});

function showMessage (message) {
  Swal.fire({
    title: 'Push Notification',
    text: message,
    icon: 'info',
    confirmButtonText: 'OK'
  });
}

function subscribe (reg) {
  reg.pushManager.getSubscription().then(function (subscription) {
    let metaObj, applicationServerKey, options;
    if (subscription) {
      return subscription;
    }

    metaObj = document.querySelector('meta[name="django-webpush-vapid-key"]');
    applicationServerKey = metaObj.content;
    options = { userVisibleOnly: true };
    if (applicationServerKey) {
      options.applicationServerKey = urlB64ToUint8Array(applicationServerKey);
    }

    reg.pushManager.subscribe(options)
      .then(function (subscription) {
        postSubscribeObj('subscribe', subscription, function (response) {
          if (response.status === 201) {
            subBtn.textContent = gettext('Unsubscribe from Push Messaging');
            subBtn.disabled = false;
            isPushEnabled = true;
            showMessage(gettext('Successfully subscribed to push notifications.'));
          }
        });
      })
      .catch(async function (err) {                           // ★ ADDED ★
        // Brave with Google-push flag OFF produces AbortError here

        if (await braveNeedsPushFlag()) {
          showMessage(
            'Brave users: open Settings ▸ Privacy & security, enable “Use Google ' +
            'services for push messaging”, then reload this page.'
          );
        } else {
          console.log(gettext('Error while subscribing to push notifications.'), err);
        }
        subBtn.disabled = false;
      });                                                     // ★ ADDED ★
  });
}

function urlB64ToUint8Array (base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

function unsubscribe (reg) {
  reg.pushManager.getSubscription().then(function (subscription) {
    if (!subscription) {
      subBtn.disabled = false;
      showMessage(gettext('Subscription is not available.'));
      return;
    }
    postSubscribeObj('unsubscribe', subscription, function (response) {
      if (response.status === 202) {
        subscription.unsubscribe()
          .then(function () {
            subBtn.textContent = gettext('Subscribe to Push Messaging');
            showMessage(gettext('Successfully unsubscribed from push notifications.'));
            isPushEnabled = false;
            subBtn.disabled = false;
          })
          .catch(function () {
            subBtn.textContent = gettext('Unsubscribe from Push Messaging');
            showMessage(gettext('Error while unsubscribing from push notifications.'));
            subBtn.disabled = false;
          });
      }
    });
  });
}

function postSubscribeObj (statusType, subscription, callback) {
  const browser = navigator.userAgent.match(/(firefox|msie|chrome|safari|trident)/ig)[0].toLowerCase();
  const user_agent = navigator.userAgent;
  const data = {
    status_type: statusType,
    subscription: subscription.toJSON(),
    browser: browser,
    user_agent: user_agent,
    group: subBtn.dataset.group
  };

  fetch(subBtn.dataset.url, {
    method: 'post',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
    credentials: 'include'
  }).then(callback);
}
