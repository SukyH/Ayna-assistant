console.log('🚀 Background Script Loading...');

// Import database operations
import { getProfileFromDB, saveAutofillMemory, getAutofillMemory } from './Database/db.js';

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('📩 Background received message:', request);

  if (request.action === 'getProfile') {
    getProfileFromDB()
      .then(profile => {
        console.log('📄 Profile retrieved:', profile);
        sendResponse(profile);
      })
      .catch(error => {
        console.error('❌ Error getting profile:', error);
        sendResponse(null);
      });
    return true;  // keep the message channel open
  }

  if (request.action === 'saveAutofillMemory') {
    saveAutofillMemory(request.label, request.value)
      .then(() => {
        console.log(`💾 Saved to memory: ${request.label} = ${request.value}`);
        sendResponse({ success: true });
      })
      .catch(error => {
        console.error('❌ Error saving to memory:', error);
        sendResponse({ success: false, error: error.message });
      });
    return true;
  }

  if (request.action === 'getAutofillMemory') {
    getAutofillMemory(request.label)
      .then(value => {
        console.log(`📤 Retrieved from memory: ${request.label} = ${value}`);
        sendResponse(value);
      })
      .catch(error => {
        console.error('❌ Error getting from memory:', error);
        sendResponse(null);
      });
    return true;
  }

  if (request.action === 'getCurrentJobURL') {
    chrome.tabs.query({ active: true, currentWindow: true }, tabs => {
      const url = tabs[0]?.url || '';
      console.log('🌐 Current active tab URL:', url);
      sendResponse({ url });
    });
    return true;
  }

  if (request.type === 'trackJobView') {
    console.log('👁️ Tracked job view:', request.data);
    sendResponse({ success: true });
    return true;
  }

  if (request.action === 'profileBuilderImport') {
    // Handle profile import from external sources (if implemented)
    try {
      handleProfileBuilderImport(sendResponse);
    } catch (error) {
      console.error('❌ Error in profileBuilderImport:', error);
      sendResponse({ success: false, error: error.message });
    }
    return true;
  }

  // Forward runAutofill requests from extension UI to content script
  if (request.action === 'runAutofill') {
    console.log('▶️ Forwarding runAutofill request to content script');
    if (sender.tab && sender.tab.id) {
      // Message came from a content script or tab context
      chrome.tabs.sendMessage(sender.tab.id, { action: 'runAutofill', siteType: request.siteType || 'generic' }, response => {
        if (chrome.runtime.lastError) {
          console.error('❌ Error forwarding runAutofill:', chrome.runtime.lastError);
          sendResponse({ success: false, message: 'Autofill content script not available' });
        } else {
          sendResponse(response);
        }
      });
    } else {
      // Message came from extension UI (no direct tab), send to current active tab
      chrome.tabs.query({ active: true, currentWindow: true }, tabs => {
        if (tabs[0]) {
          chrome.tabs.sendMessage(tabs[0].id, { action: 'runAutofill', siteType: request.siteType || 'generic' }, response => {
            if (chrome.runtime.lastError) {
              console.error('❌ Error sending runAutofill to active tab:', chrome.runtime.lastError);
              sendResponse({ success: false, message: 'No content script to handle autofill on this page' });
            } else {
              sendResponse(response);
            }
          });
        } else {
          console.warn('⚠️ No active tab found to run autofill');
          sendResponse({ success: false, message: 'No active tab to autofill' });
        }
      });
    }
    return true;
  }

  // Unknown request
  console.warn('⚠️ Unknown request:', request.action || request.type);
  sendResponse({ error: 'Unknown action' });
  return true;
});

// On extension installation
chrome.runtime.onInstalled.addListener(() => {
  console.log('✅ Extension Installed');
});

// Detect when a supported site finishes loading
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url) {
    const supportedSites = ['workday', 'greenhouse', 'lever', 'smartrecruiters', 'taleo', 'icims', 'linkedin'];
    const isSupported = supportedSites.some(site => tab.url.toLowerCase().includes(site));
    if (isSupported) {
      console.log(`🌐 Supported site detected: ${tab.url}`);
    }
  }
});

// Keep background persistent by listening for connections (fixes runtime.lastError for ports)
chrome.runtime.onConnect.addListener(port => {
  console.log('🔗 Port connected:', port.name);
  port.onDisconnect.addListener(() => {
    console.log('🔌 Port disconnected:', port.name);
  });
});
