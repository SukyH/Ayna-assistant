(async function () {
  'use strict';

  // Mark script as injected
  window.smartJobAssistantReady = true;

  // Helper to send messages to background with timeout
  const sendMessage = (message) => new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject("Timeout"), 3000);
    chrome.runtime.sendMessage(message, (response) => {
      clearTimeout(timeout);
      if (chrome.runtime.lastError) return reject(chrome.runtime.lastError.message);
      resolve(response);
    });
  });

  // Field detection patterns (updated to include separate patterns for degree and major)
  const FIELD_PATTERNS = {
    firstName: /first.*name|fname|given.*name|christian.*name/i,
    lastName: /last.*name|lname|surname|family.*name/i,
    fullName: /full.*name|name(?!.*first|.*last)/i,
    email: /email|e.*mail|mail/i,
    phone: /phone|telephone|mobile|cell|contact.*number/i,
    location: /address|street|location|city|town|zip|postal|country|state/i,
    company: /company|employer|organization|workplace/i,  // current company if not part of an experience section
    title: /title|position|job.*title|role|current.*position/i,  // current job title if not part of an experience section
    linkedin: /linkedin|linked.*in/i,
    github: /github|git.*hub/i,
    portfolio: /portfolio|website|url|personal.*site/i,
    summary: /summary|bio|about|description|cover.*letter|motivation/i,
    skills: /skills|expertise|technologies|tech.*stack/i,
    education: /school|university|college|education|institution|academy/i,
    degree: /degree|qualification|diploma|course|study/i,
    major: /major|field.*of.*study|field.*study|specialization/i
  };

  // Experience field patterns
  const EXPERIENCE_PATTERNS = {
    company: /company|employer|organization|workplace|company.*name/i,
    title: /title|position|job.*title|role(?!\s*model)|job.*position/i,
    startDate: /start.*date|from.*date|begin.*date|employment.*start|start.*month|start.*year/i,
    endDate: /end.*date|to.*date|until.*date|employment.*end|end.*month|end.*year/i,
    description: /description|responsibilities|duties|accomplishments|job.*description|summary|details/i,
    location: /location|city|address|work.*location|job.*location/i
  };

  // Project field patterns
  const PROJECT_PATTERNS = {
    name: /project.*name|project\s*title|project/i,
    description: /project.*description|overview|summary/i,
    technologies: /technology|tools|tech.*stack|technologies/i
  };

  // License/Certification field patterns
  const LICENSE_PATTERNS = {
    name: /certification|license|award|honor|credential/i,
    issuer: /issuer|organization|authority/i,
    date: /date.*(earned|issued|award|obtained)/i
  };

  // Counters for dynamic field groups (experience, project, license)
  let experienceFieldCounter = {};
  let projectFieldCounter = {};
  let licenseFieldCounter = {};

  // Collect all relevant form fields
  function getAllFormFields() {
    const fields = [];
    const selectors = [
      'input[type="text"]',
      'input[type="email"]',
      'input[type="tel"]',
      'input[type="url"]',
      'input[type="date"]',
      'input[type="month"]',
      'input:not([type])',  // inputs with no type (default text)
      'textarea',
      'select'
    ];

    // Reset counters for each run
    experienceFieldCounter = {};
    projectFieldCounter = {};
    licenseFieldCounter = {};

    selectors.forEach(selector => {
      document.querySelectorAll(selector).forEach(element => {
        // Only consider visible, enabled fields
        if (element.offsetParent !== null && !element.disabled && !element.readOnly) {
          const field = extractFieldInfo(element);
          if (field) {
            fields.push(field);
          }
        }
      });
    });

    console.log('=== FIELD ANALYSIS ===');
    console.log('Total fields found:', fields.length);
    const expFields = fields.filter(f => f.experienceFieldType);
    console.log('Experience fields:', expFields.length);
    expFields.forEach(f => {
      console.log(`${f.experienceFieldType}[${f.experienceIndex}]: "${f.label}" (${f.name || f.id})`);
    });
    const projFields = fields.filter(f => f.projectFieldType);
    const licFields = fields.filter(f => f.licenseFieldType);
    console.log('Project fields:', projFields.length);
    console.log('License/Cert fields:', licFields.length);

    return fields;
  }

  // Extract field information and determine if it belongs to experience, project, or license sections
  function extractFieldInfo(element) {
    const field = {
      field_id: generateFieldId(element),
      element: element,
      label: '',
      type: element.type || 'text',
      name: element.name || '',
      placeholder: element.placeholder || '',
      id: element.id || '',
      experienceIndex: null,
      experienceFieldType: null,
      projectIndex: null,
      projectFieldType: null,
      licenseIndex: null,
      licenseFieldType: null
    };

    // Find label text for the field
    field.label = findFieldLabel(element);
    if (!field.label || field.label.length < 2) {
      return null;
    }

    // Check if field is part of an experience section
    const expType = getExperienceFieldType(field.label);
    if (expType) {
      field.experienceFieldType = expType;
      const num = extractNumberFromField(element);
      if (num !== null) {
        field.experienceIndex = num;
        console.log(`Found numbered field: ${expType}[${num}] - ${field.label}`);
      } else {
        if (!experienceFieldCounter[expType]) {
          experienceFieldCounter[expType] = 0;
        }
        field.experienceIndex = experienceFieldCounter[expType];
        experienceFieldCounter[expType] += 1;
        console.log(`Sequential field: ${expType}[${field.experienceIndex}] - ${field.label}`);
      }
    }

    // Check if field is part of a project section
    const projType = getProjectFieldType(field.label);
    if (projType) {
      field.projectFieldType = projType;
      const num = extractNumberFromField(element);
      if (num !== null) {
        field.projectIndex = num;
        console.log(`Found numbered project field: ${projType}[${num}] - ${field.label}`);
      } else {
        if (!projectFieldCounter[projType]) {
          projectFieldCounter[projType] = 0;
        }
        field.projectIndex = projectFieldCounter[projType];
        projectFieldCounter[projType] += 1;
        console.log(`Sequential project field: ${projType}[${field.projectIndex}] - ${field.label}`);
      }
    }

    // Check if field is part of a license/certification section
    const licType = getLicenseFieldType(field.label);
    if (licType) {
      field.licenseFieldType = licType;
      const num = extractNumberFromField(element);
      if (num !== null) {
        field.licenseIndex = num;
        console.log(`Found numbered license field: ${licType}[${num}] - ${field.label}`);
      } else {
        if (!licenseFieldCounter[licType]) {
          licenseFieldCounter[licType] = 0;
        }
        field.licenseIndex = licenseFieldCounter[licType];
        licenseFieldCounter[licType] += 1;
        console.log(`Sequential license field: ${licType}[${field.licenseIndex}] - ${field.label}`);
      }
    }

    return field;
  }

  // Extract numerical index from field attributes (name, id, class, data-*)
  function extractNumberFromField(element) {
    const identifiers = [
      element.name,
      element.id,
      element.className,
      element.getAttribute('data-field-name') || '',
      element.getAttribute('data-name') || ''
    ];
    for (const id of identifiers) {
      if (!id) continue;
      const patterns = [
        id.match(/_(\d+)$/),
        id.match(/\[(\d+)\]/),
        id.match(/-(\d+)$/),
        id.match(/\.(\d+)$/),
        id.match(/(\d+)$/),
        id.match(/experience.*?(\d+)/i),
        id.match(/job.*?(\d+)/i),
        id.match(/work.*?(\d+)/i)
      ];
      for (const match of patterns) {
        if (match && match[1]) {
          const num = parseInt(match[1]);
          if (!isNaN(num)) {
            return num;
          }
        }
      }
    }
    return null;
  }

  // Determine experience field type from label text
  function getExperienceFieldType(label) {
    const text = label.toLowerCase();
    for (const [type, pattern] of Object.entries(EXPERIENCE_PATTERNS)) {
      if (pattern.test(text)) {
        return type;
      }
    }
    return null;
  }

  // Determine project field type from label text
  function getProjectFieldType(label) {
    const text = label.toLowerCase();
    for (const [type, pattern] of Object.entries(PROJECT_PATTERNS)) {
      if (pattern.test(text)) {
        return type;
      }
    }
    return null;
  }

  // Determine license/certification field type from label text
  function getLicenseFieldType(label) {
    const text = label.toLowerCase();
    for (const [type, pattern] of Object.entries(LICENSE_PATTERNS)) {
      if (pattern.test(text)) {
        return type;
      }
    }
    return null;
  }

  // Generate unique field ID for mapping results
  function generateFieldId(element) {
    const parts = [];
    if (element.id) parts.push(element.id);
    if (element.name) parts.push(element.name);
    if (element.className) parts.push(element.className.replace(/\s+/g, '-'));
    const base = parts.join('-') || 'field';
    return `${base}-${Math.random().toString(36).substr(2, 9)}`;
  }

  // Find a field's label text via associated <label>, placeholder, aria-label, etc.
  function findFieldLabel(element) {
    let text = '';

    // 1. <label for="...">
    if (element.id) {
      const labelElem = document.querySelector(`label[for="${element.id}"]`);
      if (labelElem) {
        text = labelElem.textContent.trim();
      }
    }
    // 2. Wrapping <label>
    if (!text) {
      const parentLabel = element.closest('label');
      if (parentLabel) {
        text = parentLabel.textContent.trim();
      }
    }
    // 3. aria-label attribute
    if (!text && element.getAttribute('aria-label')) {
      text = element.getAttribute('aria-label').trim();
    }
    // 4. Placeholder text as label
    if (!text && element.placeholder) {
      text = element.placeholder.trim();
    }
    // 5. Nearby text nodes (e.g., within same container)
    if (!text) {
      const parent = element.parentElement;
      if (parent) {
        const walker = document.createTreeWalker(parent, NodeFilter.SHOW_TEXT, null, false);
        let node;
        const texts = [];
        while ((node = walker.nextNode())) {
          const nodeText = node.textContent.trim();
          if (nodeText && nodeText.length > 1 && nodeText.length < 100) {
            texts.push(nodeText);
          }
        }
        if (texts.length > 0) {
          text = texts[0];
        }
      }
    }
    // 6. Fallback: use name attribute
    if (!text && element.name) {
      text = element.name.replace(/[_-]/g, ' ').trim();
    }

    return cleanLabel(text);
  }

  // Clean label text by removing generic prompts and special characters
  function cleanLabel(label) {
    if (!label) return '';
    label = label.replace(/^(please\s+)?(enter\s+)?(your\s+)?/i, '');
    label = label.replace(/\s*(required|\*|\(required\))/i, '');
    label = label.replace(/[*:()[\]{}]/g, '');
    return label.trim();
  }

  // Get profile
  async function getProfile() {
    const res = await sendMessage({ action: 'getProfile' });
    return res || {};
  }

  // Get memory
  async function getAutofillMemory(label) {
    try {
      return await sendMessage({ action: 'getAutofillMemory', label });
    } catch {
      return null;
    }
  }
// Save a filled field's value to memory for future usage
 async function saveToAutofillMemory(label, value) {
   return new Promise((resolve, reject) => {
     chrome.runtime.sendMessage({ action: 'saveAutofillMemory', label, value }, response => {
       if (chrome.runtime.lastError) {
         console.error('Runtime error saving to memory:', chrome.runtime.lastError);
         return reject(new Error(chrome.runtime.lastError.message));
       }
       if (response && response.success !== undefined) {
         // If background provided a success status
         return response.success ? resolve(response) : reject(new Error(response.error || 'Failed to save to memory'));
       }
       resolve(response);
     });
   });
 }


  // Call server autofill
  async function callServerAutofill(fields, profile) {
    const res = await fetch('http://localhost:8000/autofill', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        fields: fields.map(field => ({
          field_id: field.field_id,
          label: field.label,
          type: field.type,
          name: field.name,
          placeholder: field.placeholder,
          experienceIndex: field.experienceIndex,
          experienceFieldType: field.experienceFieldType,
          projectIndex: field.projectIndex,
          projectFieldType: field.projectFieldType,
          licenseIndex: field.licenseIndex,
          licenseFieldType: field.licenseFieldType
        })),
        profile: profile
      })
    });
    if (!res.ok) return null;
    return await res.json();
  }

  // Perform client-side autofill using the local profile data
  function clientSideAutofill(fields, profile) {
    const results = {};
    // Flatten profile for easy lookup
    const flatProfile = {
      first_name: profile.fullName?.split(' ')[0] || '',
      last_name: profile.fullName?.split(' ').slice(1).join(' ') || '',
      full_name: profile.fullName || '',
      email: profile.email || '',
      phone: profile.phone || '',
      location: profile.location || '',
      linkedin: profile.linkedin || '',
      github: profile.github || '',
      portfolio: profile.portfolio || '',
      summary: profile.summary || '',
      skills: Array.isArray(profile.skills) ? profile.skills.join(', ') : (profile.skills || ''),
      education: profile.education?.[0]?.school || '',
      degree: profile.education?.[0] ? `${profile.education[0].degree || ''} ${profile.education[0].field || ''}`.trim() : '',
      major: profile.education?.[0]?.field || '',
      experiences: profile.experience || [],
      projects: profile.projects || profile.personalProjects || [],
      certifications: profile.certifications || profile.licenses || profile.awards || []
    };

    console.log('=== AUTOFILL PROCESS ===');
    console.log('Experiences available:', flatProfile.experiences.length);
    flatProfile.experiences.forEach((exp, i) => {
      console.log(`Experience[${i}]: ${exp.company || 'N/A'} - ${exp.position || exp.title || 'N/A'}`);
    });

    fields.forEach(field => {
      const labelText = field.label.toLowerCase();

      // Experience fields: retrieve from experiences array
      if (field.experienceFieldType && field.experienceIndex !== null) {
        const val = getExperienceValue(field.experienceFieldType, field.experienceIndex, flatProfile.experiences);
        if (val) {
          results[field.field_id] = val;
          return;
        }
      }

      // Project fields: retrieve from projects array
      if (field.projectFieldType && field.projectIndex !== null) {
        const val = getProjectValue(field.projectFieldType, field.projectIndex, flatProfile.projects);
        if (val) {
          results[field.field_id] = val;
          return;
        }
      }

      // License/Certification fields: retrieve from certifications array
      if (field.licenseFieldType && field.licenseIndex !== null) {
        const val = getLicenseValue(field.licenseFieldType, field.licenseIndex, flatProfile.certifications);
        if (val) {
          results[field.field_id] = val;
          return;
        }
      }

      // General fields: match via FIELD_PATTERNS
      for (const [key, pattern] of Object.entries(FIELD_PATTERNS)) {
        if (pattern.test(labelText)) {
          let value = '';
          if (key === 'company') {
            // If generic "Company" field (not in experience section), use first experience's company
            value = flatProfile.experiences[0]?.company || '';
          } else if (key === 'title') {
            // If generic "Title" field (not in experience section), use first experience's title/position
            value = flatProfile.experiences[0]?.position || flatProfile.experiences[0]?.title || '';
          } else {
            const profileKey = mapFieldToProfile(key);
            value = flatProfile[profileKey];
          }
          if (value && value.toString().trim()) {
            results[field.field_id] = value;
          }
          break;
        }
      }
    });
    return results;
  }

  // Get experience value from profile for a given field type and index
  function getExperienceValue(type, idx, experiences) {
    if (!experiences || idx >= experiences.length) return '';
    const exp = experiences[idx];
    if (!exp) return '';
    switch (type) {
      case 'company':     return exp.company || '';
      case 'title':       return exp.position || exp.title || '';
      case 'startDate':   return formatDateForField(exp.startDate) || '';
      case 'endDate':     return exp.current ? 'Present' : (formatDateForField(exp.endDate) || '');
      case 'description': return exp.description || '';
      case 'location':    return exp.location || '';
      default:            return '';
    }
  }

  // Get project value from profile for a given field type and index
  function getProjectValue(type, idx, projects) {
    if (!projects || idx >= projects.length) return '';
    const proj = projects[idx];
    if (!proj) return '';
    switch (type) {
      case 'name':        return proj.name || proj.title || '';
      case 'description': return proj.description || proj.summary || '';
      case 'technologies':
        if (proj.technologies) {
          return Array.isArray(proj.technologies) ? proj.technologies.join(', ') : proj.technologies;
        }
        if (proj.tools) {
          return Array.isArray(proj.tools) ? proj.tools.join(', ') : proj.tools;
        }
        return '';
      default: return '';
    }
  }

  // Get license/certification value from profile for a given field type and index
  function getLicenseValue(type, idx, certifications) {
    if (!certifications || idx >= certifications.length) return '';
    const cert = certifications[idx];
    if (!cert) return '';
    switch (type) {
      case 'name':   return cert.name || cert.title || '';
      case 'issuer': return cert.issuer || cert.authority || cert.organization || '';
      case 'date': {
        let dateVal = cert.date || '';
        // If stored date is in YYYY-MM-DD format, convert it to MM/YYYY
        if (dateVal && /^\d{4}-\d{2}-\d{2}$/.test(dateVal)) {
          dateVal = formatDateForField(dateVal);
        }
        return dateVal;
      }
      default: return '';
    }
  }

  // Format a date string to "MM/YYYY"
  function formatDateForField(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) {
      // If not a full date, try to parse "YYYY-MM" or return original
      const parts = dateStr.match(/^(\d{4})-(\d{2})$/);
      if (parts) {
        return `${parts[2]}/${parts[1]}`;  // "YYYY-MM" -> "MM/YYYY"
      }
      return dateStr;
    }
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${month}/${year}`;
  }

  // Map a field pattern key to the corresponding flatProfile key
  function mapFieldToProfile(type) {
    const map = {
      firstName: 'first_name',
      lastName: 'last_name',
      fullName: 'full_name',
      email: 'email',
      phone: 'phone',
      location: 'location',
      linkedin: 'linkedin',
      github: 'github',
      portfolio: 'portfolio',
      summary: 'summary',
      skills: 'skills',
      education: 'education',
      degree: 'degree',
      major: 'major'
    };
    return map[type] || type;
  }

  // Fill form fields with the given values and simulate user input events
  function fillFields(fieldsMap, autofillResults) {
    let filledCount = 0;
    const usedExpIndices = new Set();

    console.log('=== FILLING FIELDS ===');
    for (const [fieldId, value] of Object.entries(autofillResults)) {
      const field = fieldsMap[fieldId];
      if (!field || !field.element) continue;
      if (value === null || value === undefined) continue;
      if (typeof value === 'string' && !value.trim()) continue;

      // Avoid filling duplicate experience entries more than once per field type
      if (field.experienceFieldType && field.experienceIndex !== null) {
        const uniqueKey = `${field.experienceFieldType}_${field.experienceIndex}`;
        if (usedExpIndices.has(uniqueKey)) {
          continue;
        }
        usedExpIndices.add(uniqueKey);
      }

      const element = field.element;
      let fillValue = value;
      console.log(`Filling "${field.label}" with "${fillValue}"`);

      // If input type is date or month, adjust "MM/YYYY" to required format
      if (element.type === 'date') {
        if (typeof fillValue === 'string' && /^\d{2}\/\d{4}$/.test(fillValue)) {
          const [mm, yyyy] = fillValue.split('/');
          fillValue = `${yyyy}-${mm}-01`;
        }
      } else if (element.type === 'month') {
        if (typeof fillValue === 'string' && /^\d{2}\/\d{4}$/.test(fillValue)) {
          const [mm, yyyy] = fillValue.split('/');
          fillValue = `${yyyy}-${mm}`;
        }
      }

      if (element.tagName.toLowerCase() === 'select') {
        // For select dropdowns, set the value and trigger change
        element.focus();
        element.value = fillValue;
        if (!element.value || element.value !== fillValue) {
          // If direct value assignment didn't match an option, try matching by text
          const options = Array.from(element.options);
          const match = options.find(opt => opt.textContent.trim().toLowerCase() === String(fillValue).toLowerCase());
          if (match) {
            match.selected = true;
          }
        }
        element.dispatchEvent(new Event('change', { bubbles: true }));
        element.blur();
      } else {
        // For text inputs and textareas, simulate key events and input
        element.focus();
        if (typeof fillValue === 'string' && fillValue.length > 0) {
          const firstChar = fillValue.charAt(0);
          const lastChar = fillValue.charAt(fillValue.length - 1);
          const firstCode = firstChar.charCodeAt(0);
          const lastCode = lastChar.charCodeAt(0);
          element.dispatchEvent(new KeyboardEvent('keydown', { key: firstChar, code: firstChar, keyCode: firstCode, which: firstCode, bubbles: true }));
          element.dispatchEvent(new KeyboardEvent('keypress', { key: firstChar, code: firstChar, keyCode: firstCode, which: firstCode, bubbles: true }));
          element.value = fillValue;
          element.dispatchEvent(new Event('input', { bubbles: true }));
          element.dispatchEvent(new KeyboardEvent('keyup', { key: lastChar, code: lastChar, keyCode: lastCode, which: lastCode, bubbles: true }));
        } else {
          element.value = fillValue;
          element.dispatchEvent(new Event('input', { bubbles: true }));
        }
        element.dispatchEvent(new Event('change', { bubbles: true }));
        element.blur();
      }

      // Save filled value to memory (asynchronous, no need to await)
      saveToAutofillMemory(field.label, fillValue).catch(err => {
        console.warn(`Error saving memory for ${field.label}:`, err);
      });
      filledCount++;
    }
    console.log(`✅ Filled ${filledCount} fields`);
    return filledCount;
  }

  // Main autofill logic
  async function runAutofill() {
    const fields = getAllFormFields();
    const profile = await getProfile();
     
    // Map fields by field_id for quick lookup
    const fieldsMap = {};
    fields.forEach(f => { fieldsMap[f.field_id] = f; });

    const memoryResults = {};
    for (const field of fields) {
      const mem = await getAutofillMemory(field.label);
      if (mem) memoryResults[field.field_id] = mem;
    }

    // Determine which fields still need filling after using memory
    let autofillResults = { ...memoryResults };
    const remainingFields = fields.filter(f => !autofillResults[f.field_id]);

    if (remainingFields.length > 0) {
      // Attempt server-side autofill first
      const serverResults = await callServerAutofill(remainingFields, profile);
      if (serverResults) {
        console.log('ℹ️ Server autofill provided some field values');
        autofillResults = { ...autofillResults, ...serverResults };
      } else {
        // Fallback to local profile autofill
        console.log('🔄 Falling back to client-side autofill for remaining fields');
        const clientResults = clientSideAutofill(remainingFields, profile);
        autofillResults = { ...autofillResults, ...clientResults };
      }
    }

    // Fill the fields and return summary
    const filledCount = fillFields(fieldsMap, autofillResults);
    return {
      success: true,
      filledFields: filledCount,
      totalFields: fields.length,
      message: `Filled ${filledCount} out of ${fields.length} fields`
    };
  }

  // Message listener
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'ping') {
      sendResponse({ status: 'ready' });
      return true;
    }
    if (request.action === 'runAutofill') {
      runAutofill(request.siteType)
        .then(result => sendResponse(result))
        .catch(err => sendResponse({ success: false, message: err.message }));
      return true;
    }
  });
})();