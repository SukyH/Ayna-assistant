// src/components/Popup.jsx
import React, { useState, useEffect } from 'react';
import { Text, Stack, PrimaryButton, ThemeProvider } from '@fluentui/react';
import { ClassyTheme } from '../themes/ClassyTheme';
import { getProfileFromDB } from '../Database/db';

function Popup() {
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [currentTab, setCurrentTab] = useState(null);
  const [hasProfile, setHasProfile] = useState(false);

  useEffect(() => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      setCurrentTab(tabs[0]);
    });
    checkProfile();
  }, []);

  const checkProfile = async () => {
    try {
      const profile = await getProfileFromDB();
      setHasProfile(!!profile);
    } catch {
      setHasProfile(false);
    }
  };

  const detectSite = (url = '') => {
    if (url.includes('workday')) return 'Workday';
    if (url.includes('greenhouse')) return 'Greenhouse';
    if (url.includes('lever')) return 'Lever';
    if (url.includes('smartrecruiters')) return 'SmartRecruiters';
    if (url.includes('taleo')) return 'Taleo';
    if (url.includes('icims')) return 'iCIMS';
    if (url.includes('linkedin')) return 'LinkedIn';
    return 'Unknown';
  };

  const handleAutofillClick = async () => {
    if (!currentTab || !hasProfile || isLoading) return;
  
    setIsLoading(true);
    setStatus('🔄 Injecting and running autofill...');
  
    try {
      const siteType = detectSite(currentTab.url);
      const tabId = currentTab.id;
  
      const injectScript = async () => {
        await chrome.scripting.executeScript({
          target: { tabId },
          files: ['contentScript.js'],
        });
      };
  
      const waitForReady = async () => {
        const maxAttempts = 10;
        let attempts = 0;
        while (attempts < maxAttempts) {
          try {
            const response = await new Promise((resolve) =>
              chrome.tabs.sendMessage(tabId, { action: 'ping' }, resolve)
            );
            if (response?.status === 'ready') return true;
          } catch {}
          await new Promise((res) => setTimeout(res, 300));
          attempts++;
        }
        throw new Error("Content script didn't respond");
      };
  
      // Inject and wait for ready
      await injectScript();
      await waitForReady();
  
      // Run autofill
      const autofillResponse = await new Promise((resolve) =>
        chrome.tabs.sendMessage(tabId, { action: 'runAutofill', siteType }, resolve)
      );
  
      if (chrome.runtime.lastError) {
        throw new Error(chrome.runtime.lastError.message);
      }
  
      if (autofillResponse?.success) {
        setStatus(`✅ Autofilled ${autofillResponse.fieldsCount} fields.`);
      } else {
        setStatus(`⚠️ ${autofillResponse?.message || 'Autofill finished with warnings.'}`);
      }
    } catch (error) {
      console.error("Autofill Error:", error);
      setStatus(`❌ ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };
  

  return (
    <ThemeProvider theme={ClassyTheme}>
      <Stack tokens={{ childrenGap: 12 }} style={{ padding: 20, width: 320 }}>
        <Text variant="large">🚀 Smart Job Assistant</Text>
        <Text variant="small">Current Site: {detectSite(currentTab?.url)}</Text>

        <Text style={{ color: hasProfile ? 'green' : 'red' }}>
          {hasProfile ? '✅ Profile Found' : '❌ No Profile Found'}
        </Text>

      

        <PrimaryButton
          text={isLoading ? 'Filling...' : '📝 Autofill This Page'}
          onClick={handleAutofillClick}
          disabled={!hasProfile || isLoading}
        />

        {status && <Text variant="small">{status}</Text>}

        <Text variant="xSmall" style={{ marginTop: 8, color: ClassyTheme.palette.neutralSecondary }}>
          Supported: Workday, Greenhouse, Lever, SmartRecruiters, Taleo, iCIMS, LinkedIn
        </Text>
      </Stack>
    </ThemeProvider>
  );
}

export default Popup;
