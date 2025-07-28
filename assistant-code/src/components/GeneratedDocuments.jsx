import {
  Text,
  Stack,
  PrimaryButton,
  DefaultButton,
  TextField,
  ThemeProvider,
} from "@fluentui/react";
import { ClassyTheme } from "../themes/ClassyTheme";
import { useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { getProfileFromDB, getResumeFromDB } from "../Database/db";

const GeneratedDocuments = () => {
  const { state } = useLocation();
  const navigate = useNavigate();
  const [resume, setResume] = useState("");
  const [coverLetter, setCoverLetter] = useState("");
  const [loading, setLoading] = useState(true);
  const [refineFeedback, setRefineFeedback] = useState("");
  const [resumeRefinedMsg, setResumeRefinedMsg] = useState("");
  const [coverRefinedMsg, setCoverRefinedMsg] = useState("");
  const [matchData, setMatchData] = useState("");

  const generateDocuments = async () => {
    try {
      const profile = await getProfileFromDB();
      const resumeFile = await getResumeFromDB();
      const jobData = state?.jobData;

      if (!profile || !jobData) throw new Error("Missing data.");
      const payload = { profile, job: jobData, resume: resumeFile || null };

      const [res1, res2] = await Promise.all([
        fetch("http://localhost:8000/generate-resume", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }),
        fetch("http://localhost:8000/generate-coverletter", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }),
      ]);

      const resumeData = await res1.json();
      const coverLetterData = await res2.json();

      setResume(resumeData.resume || "");
      setCoverLetter(coverLetterData.coverletter || "");
      localStorage.setItem("generatedResume", resumeData.resume || "");
      localStorage.setItem("generatedCoverLetter", coverLetterData.coverletter || "");
    } catch (err) {
      console.error("Generation failed:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const savedMatch = localStorage.getItem("lastMatchScore");
    if (savedMatch) setMatchData(JSON.parse(savedMatch));

    const savedResume = localStorage.getItem("generatedResume");
    const savedCover = localStorage.getItem("generatedCoverLetter");

    if (savedResume && savedCover) {
      setResume(savedResume);
      setCoverLetter(savedCover);
      setLoading(false);
    } else {
      generateDocuments();
    }
  }, [state]);

  const downloadPDF = async (endpoint, filename) => {
    try {
      const profile = await getProfileFromDB();
      const resumeFile = await getResumeFromDB();
      const jobData = state?.jobData;

      const payload = { profile, job: jobData, resume: resumeFile || null };

      const res = await fetch(`http://localhost:8000/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      link.click();
    } catch (err) {
      console.error("PDF download failed:", err);
    }
  };

  const handleRefine = async (type) => {
    const profile = await getProfileFromDB();
    const jobData = state?.jobData;

    const payload = {
      profile,
      job: jobData,
      resume,
      feedback: refineFeedback,
      ...(type === "cover" && { coverletter: coverLetter }),
    };

    const res = await fetch(
      `http://localhost:8000/refine-${type === "cover" ? "coverletter" : "resume"}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }
    );

    const data = await res.json();
    if (type === "cover") {
      setCoverLetter(data.refined_coverletter);
      setCoverRefinedMsg("Cover letter refined successfully.");
      localStorage.setItem("generatedCoverLetter", data.refined_coverletter);
    } else {
      setResume(data.refined_resume);
      setResumeRefinedMsg("Resume refined successfully.");
      localStorage.setItem("generatedResume", data.refined_resume);
    }

    setRefineFeedback("");
  };

  return (
    <ThemeProvider theme={ClassyTheme}>
      <Stack
        styles={{
          root: {
            background: ClassyTheme.palette.white,
            minHeight: "100vh",
            padding: "32px",
          },
        }}
      >
        <Text
          variant="xxLarge"
          styles={{
            root: {
              textAlign: "center",
              marginBottom: 32,
              color: ClassyTheme.palette.themeDark,
            },
          }}
        >
          Generated Documents
        </Text>

        {state?.jobData && (
          <Stack horizontal horizontalAlign="center" style={{ marginBottom: 24 }}>
            <PrimaryButton
              text="Regenerate for New Job"
              styles={{
                root: {
                  background: ClassyTheme.palette.themePrimary,
                  color: "white",
                },
                rootHovered: {
                  background: ClassyTheme.palette.themeSecondary,
                },
              }}
              onClick={() => {
                localStorage.removeItem("generatedResume");
                localStorage.removeItem("generatedCoverLetter");
                setLoading(true);
                generateDocuments();
              }}
            />
          </Stack>
        )}

        {loading ? (
          <Text>Generating documents...</Text>
        ) : (
          <Stack tokens={{ childrenGap: 24 }}>
            <Stack>
              <Text variant="xLarge" styles={{ root: { color: ClassyTheme.palette.themePrimary } }}>
                Resume
              </Text>
              <pre
                style={{
                  backgroundColor: ClassyTheme.palette.neutralLighter,
                  padding: "16px",
                  borderRadius: "6px",
                  maxHeight: "500px",
                  overflowY: "auto",
                  whiteSpace: "pre-wrap",
                }}
              >
                {resume}
              </pre>
            </Stack>

            <Stack>
              <Text variant="xLarge" styles={{ root: { color: ClassyTheme.palette.themePrimary } }}>
                Cover Letter
              </Text>
              <pre
                style={{
                  backgroundColor: ClassyTheme.palette.neutralLighter,
                  padding: "16px",
                  borderRadius: "6px",
                  whiteSpace: "pre-wrap",
                }}
              >
                {coverLetter}
              </pre>
            </Stack>

            <Stack horizontal wrap tokens={{ childrenGap: 12 }}>
              <DefaultButton onClick={() => downloadPDF("download-resume-pdf", "resume.pdf")}>
                Download Resume PDF
              </DefaultButton>
              <DefaultButton onClick={() => downloadPDF("download-coverletter-pdf", "coverletter.pdf")}>
                Download Cover Letter PDF
              </DefaultButton>
              <DefaultButton onClick={() => navigate("/")}>Back to Profile</DefaultButton>
              <DefaultButton onClick={() => navigate("/analyze-job")}>Back to Job Analyzer</DefaultButton>
            </Stack>

            {(resume || coverLetter) && (
              <Stack>
                <Text variant="large">Refine Resume or Cover Letter</Text>
                <TextField
                  multiline
                  rows={4}
                  placeholder="Add more metrics, make it sound more formal..."
                  value={refineFeedback}
                  onChange={(_, val) => setRefineFeedback(val)}
                />
                <Stack horizontal tokens={{ childrenGap: 10 }}>
                  <PrimaryButton onClick={() => handleRefine("resume")}>Refine Resume</PrimaryButton>
                  <PrimaryButton onClick={() => handleRefine("cover")}>Refine Cover Letter</PrimaryButton>
                </Stack>
                {resumeRefinedMsg && <Text>{resumeRefinedMsg}</Text>}
                {coverRefinedMsg && <Text>{coverRefinedMsg}</Text>}
              </Stack>
            )}
          </Stack>
        )}
      </Stack>
    </ThemeProvider>
  );
};

export default GeneratedDocuments;
