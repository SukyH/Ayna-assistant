import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Stack,
  TextField,
  PrimaryButton,
  DefaultButton,
  Toggle,
  Text,
  ThemeProvider,
  initializeIcons
} from '@fluentui/react';
import { ClassyTheme } from '../themes/ClassyTheme';
import nlp from 'compromise';


const JobAnalyzer = () => {
  const [tab, setTab] = useState("url");
  const [jobText, setJobText] = useState("");
  const [jobURL, setJobURL] = useState("");
  const [parsed, setParsed] = useState(null);
  const [error, setError] = useState("");
  const [saveSuccess, setSaveSuccess] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const savedJob = localStorage.getItem("lastAnalyzedJob");
    if (savedJob) setParsed(JSON.parse(savedJob));
  }, []);

  useEffect(() => {
    if (saveSuccess) {
      const timer = setTimeout(() => setSaveSuccess(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [saveSuccess]);

  const handleCurrentTabAnalyze = () => {
    setError("");
    setParsed(null);
    chrome.runtime.sendMessage({ action: "getCurrentJobURL" }, async (response) => {
      const currentUrl = response?.url || "";
      if (!currentUrl) return setError("Could not detect job URL.");
      await analyzeJobFromURL(currentUrl);
    });
  };

const normalizeLinkedInJobURL = (url) => {
  try {
    const parsed = new URL(url);

    const isLinkedIn = parsed.hostname.includes("linkedin.com");
    const jobId = parsed.searchParams.get("currentJobId");

    if (isLinkedIn && jobId) {
      return `https://www.linkedin.com/jobs/view/${jobId}/`;
    }

    // If it's already a job view URL, return as-is
    if (isLinkedIn && parsed.pathname.includes("/jobs/view/")) {
      return url;
    }

    return url;
  } catch {
    return url;
  }
};


  const analyzeJobFromURL = async (url) => {
    const normalizedURL = normalizeLinkedInJobURL(url);
    try {
      const res = await fetch("http://localhost:8000/scrape-job", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: normalizedURL }),
      });
      const data = await res.json();
      setParsed(data);
      localStorage.setItem("lastAnalyzedJob", JSON.stringify(data));
    } catch (err) {
      setError(err.message || "Something went wrong.");
    }
  };

  const handleAnalyze = async () => {
    setError("");
    setParsed(null);
    let endpoint = "";
    let payload = {};

    if (tab === "url") {
      if (!jobURL.trim()) return setError("Please enter a job URL.");
      endpoint = "http://localhost:8000/scrape-job";
      payload = { url: normalizeLinkedInJobURL(jobURL) };
    } else {
      if (!jobText.trim()) return setError("Please paste a job description.");
      endpoint = "http://localhost:8000/parse-job-text";
      payload = { text: jobText };
    }

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      const dataWithMeta = {
        ...data,
        url: jobURL,
        title: data.title || "Untitled",
        company: data.company || "Unknown"
      };

      setParsed(dataWithMeta);
      localStorage.setItem("lastAnalyzedJob", JSON.stringify(dataWithMeta));
    } catch (err) {
      setError(err.message || "Something went wrong.");
    }
  };

  const saveJobToTracker = async () => {
    if (!parsed) return;
    const payload = {
      title: parsed.title || "Untitled",
      company: parsed.company || "Unknown",
      url: parsed.url || null,
      status: "Saved",
      notes: "",     
      feedback: "",  
      reminder_date: null
    };
    
    

    try {
      console.log("Sending payload:", payload);
      const res = await fetch("http://localhost:8000/job-tracker/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error("Failed to save job.");
      alert(`Job "${parsed.title}" saved successfully!`);
      setSaveSuccess(true);
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  return (
    <ThemeProvider theme={ClassyTheme}>
      <Stack tokens={{ childrenGap: 16 }} styles={{ root: { padding: 32 } }}>
        <Text variant="xxLarge">📄 Job Description Analyzer</Text>

        <Stack horizontal tokens={{ childrenGap: 12 }}>
          <DefaultButton text="Analyze from URL" onClick={() => setTab("url")} />
          <DefaultButton text="Paste Job Description" onClick={() => setTab("paste")} />
          <PrimaryButton text="Analyze Current Tab" onClick={handleCurrentTabAnalyze} />
        </Stack>

        {tab === "url" ? (
          <TextField
            label="Job URL"
            value={jobURL}
            onChange={(_, v) => setJobURL(v)}
          />
        ) : (
          <TextField
            label="Paste Description"
            multiline
            rows={8}
            value={jobText}
            onChange={(_, v) => setJobText(v)}
          />
        )}

        {error && <Text style={{ color: 'red' }}>{error}</Text>}

        <PrimaryButton text="Analyze" onClick={handleAnalyze} />

        {parsed && (
          <Stack tokens={{ childrenGap: 12 }} styles={{ root: { background: ClassyTheme.palette.neutralLighter, padding: 16, borderRadius: 8 } }}>
            <Text variant="xLarge">Extracted Job Info</Text>
            <Text><strong>Title:</strong> {parsed.title}</Text>
            <Text><strong>Company:</strong> {parsed.company}</Text>
            <Text><strong>Skills:</strong> {parsed.skills?.join(', ') || "None"}</Text>
           <Text><strong>Responsibilities:</strong></Text>
            <ul>
              {parsed.responsibilities?.length ? (
                parsed.responsibilities.map((r, i) => <li key={i}>{r}</li>)
              ) : (
                <li>None detected.</li>
              )}
            </ul>

            <Stack horizontal tokens={{ childrenGap: 8 }}>
              <PrimaryButton text="Generate Resume & Cover Letter" onClick={() => navigate("/generate-documents", { state: { jobData: parsed } })} />
              <DefaultButton text="Match Score" onClick={() => navigate("/match-score", { state: { jobData: parsed } })} />
              <DefaultButton text="Save Job" onClick={saveJobToTracker} />
              <DefaultButton text="Back to Profile" onClick={() => navigate("/")} />
            </Stack>
          </Stack>
        )}
      </Stack>
    </ThemeProvider>
  );
};

export default JobAnalyzer;
