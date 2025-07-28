import { openDB } from './idb.js';

const DB_NAME = 'SmartJobAssistant';
const DB_VERSION = 3;
const STORE_PROFILE = 'profile';
const STORE_JOB_TRACKER = 'jobTracker';
const STORE_FEEDBACK = 'userFeedback';
const STORE_RESUME = 'resumes';
const STORE_ENRICHED = 'enrichedProfile';
const STORE_AUTOFILL_MEMORY = 'autofillMemory';



export const getDB = async () => {
  return await openDB(DB_NAME, DB_VERSION, {
    upgrade(db, oldVersion, newVersion, transaction) {
      if (!db.objectStoreNames.contains(STORE_PROFILE)) {
        db.createObjectStore(STORE_PROFILE);
      }
        
      if (!db.objectStoreNames.contains(STORE_JOB_TRACKER)) {
        db.createObjectStore(STORE_JOB_TRACKER, { keyPath: 'id', autoIncrement: true });
      }
      if (!db.objectStoreNames.contains(STORE_FEEDBACK)) {
        db.createObjectStore(STORE_FEEDBACK, { keyPath: 'id', autoIncrement: true });
      }
      if (!db.objectStoreNames.contains(STORE_RESUME)) {
        db.createObjectStore(STORE_RESUME);
      }
      if (!db.objectStoreNames.contains(STORE_ENRICHED)) {
        db.createObjectStore(STORE_ENRICHED);
      }

      if (!db.objectStoreNames.contains(STORE_AUTOFILL_MEMORY)) {
  db.createObjectStore(STORE_AUTOFILL_MEMORY);
      } 

    },
  });
};

export const saveAutofillMemory = async (label, value) => {
  const db = await getDB();
  await db.put(STORE_AUTOFILL_MEMORY, value, label);
};

export const getAutofillMemory = async (label) => {
  const db = await getDB();
  return await db.get(STORE_AUTOFILL_MEMORY, label);
};

// Profile operations
export const saveProfileToDB = async (profile) => {
  try {
    const db = await getDB();
    await db.put(STORE_PROFILE, profile, 'user');
  } catch (error) {
    console.error('Failed to save profile to DB:', error);
  }
};


export const getAllAutofillMemory = async () => {
  try {
    const db = await getDB();
    const all = await db.getAll(STORE_AUTOFILL_MEMORY);
    console.log(`Retrieved all autofill memory: ${all.length} entries`);
    return all;
  } catch (error) {
    console.error('❌ Failed to retrieve all autofill memory:', error);
    return [];
  }
};

export const clearAutofillMemory = async () => {
  try {
    const db = await getDB();
    await db.clear(STORE_AUTOFILL_MEMORY);
    console.log(' Cleared all autofill memory');
  } catch (error) {
    console.error('❌ Failed to clear autofill memory:', error);
  }
};

export const getProfileFromDB = async () => {
  try {
    const db = await getDB();
    return await db.get(STORE_PROFILE, 'user');
  } catch (error) {
    console.error('Failed to retrieve profile from DB:', error);
    return null;
  }
};


//Resume operations
export const saveResumeToDB = async (resumeMeta) => {
  try {
    const db = await getDB();
    await db.put(STORE_RESUME, resumeMeta, 'user-resume');
    console.log('Resume saved successfully');
  } catch (error) {
    console.error('Failed to save resume to DB:', error);
    throw error;
  }
};

export const getResumeFromDB = async () => {
  try {
    const db = await getDB();
    const resume = await db.get(STORE_RESUME, 'user-resume');
    console.log('Resume retrieved:', resume);
    return resume;
  } catch (error) {
    console.error('Failed to retrieve resume from DB:', error);
    return null;
  }
};

export const deleteResumeFromDB = async () => {
  try {
    const db = await getDB();
    await db.delete(STORE_RESUME, 'user-resume');
    console.log('Resume deleted successfully');
  } catch (error) {
    console.error('Failed to delete resume from DB:', error);
  }
};

// Job tracker operations
export const saveJobApplication = async (jobData) => {
  try {
    const db = await getDB();
    await db.add(STORE_JOB_TRACKER, jobData);
  } catch (error) {
    console.error('Failed to save job application:', error);
  }
};

export const getAllJobApplications = async () => {
  try {
    const db = await getDB();
    return await db.getAll(STORE_JOB_TRACKER);
  } catch (error) {
    console.error('Failed to retrieve job applications:', error);
    return [];
  }
};

// User feedback operations
export const addUserFeedback = async (entry) => {
  try {
    const db = await getDB();
    await db.add(STORE_FEEDBACK, entry);
  } catch (error) {
    console.error('Failed to add user feedback:', error);
  }
};

export const getAllUserFeedback = async () => {
  try {
    const db = await getDB();
    return await db.getAll(STORE_FEEDBACK);
  } catch (error) {
    console.error('Failed to retrieve user feedback:', error);
    return [];
  }
};

//Enriched profile operations
export const saveEnrichedProfileToDB = async (profile) => {
  try {
    const db = await getDB();
    await db.put(STORE_ENRICHED, profile, 'latest');
    console.log('Enriched profile saved successfully');
  } catch (error) {
    console.error('Failed to save enriched profile:', error);
    throw error;
  }
};

export const getEnrichedProfileFromDB = async () => {
  try {
    const db = await getDB();
    const profile = await db.get(STORE_ENRICHED, 'latest');
    console.log('Enriched profile retrieved:', profile);
    return profile;
  } catch (error) {
    console.error('Failed to retrieve enriched profile:', error);
    return null;
  }
};
