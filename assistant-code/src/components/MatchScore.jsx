import { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { getProfileFromDB } from "../Database/db";
import {
  ThemeProvider,
  Stack,
  Text,
  DefaultButton,
  PrimaryButton,
  TextField,
  Separator,
  MessageBar,
  MessageBarType,
} from "@fluentui/react";
import { ClassyTheme } from "../themes/ClassyTheme";

export default function MatchScore() {
  const { state } = useLocation();
  const job = state?.jobData || {};
  const [profile, setProfile] = useState(null);
  const [result, setResult] = useState(null);
  const [userFeedback, setUserFeedback] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const storedProfile = await getProfileFromDB();
        console.log("Raw profile from DB:", storedProfile); // Debug log
        
        // ✅ DON'T modify the profile structure - just use it exactly as stored
        if (storedProfile) {
          setProfile(storedProfile);
        } else {
          setProfile(null);
          setStatusMessage("❌ No profile found. Please create a profile first.");
        }
      } catch (error) {
        console.error("Error fetching profile:", error);
        setStatusMessage("❌ Error loading profile.");
        setProfile(null);
      }
    };
    
    fetchProfile();
  }, []);

  useEffect(() => {
    if (profile && job && Object.keys(job).length > 0) {
      // Check if we have cached results for this exact job
      const savedJob = JSON.parse(localStorage.getItem("lastAnalyzedJob") || "{}");
      if (savedJob?.title === job?.title && savedJob?.company === job?.company) {
        const savedScore = JSON.parse(localStorage.getItem("lastMatchScore") || "{}");
        if (savedScore?.overall_score !== undefined) {
          setResult(savedScore);
          return;
        }
      }
      runMatchScore();
    }
  }, [profile, job]);

  const runMatchScore = async () => {
    if (!profile) {
      setStatusMessage("❌ Profile not loaded yet.");
      return;
    }

    if (!job || Object.keys(job).length === 0) {
      setStatusMessage("❌ No job data available.");
      return;
    }

    setLoading(true);
    setStatusMessage("🔄 Computing match score...");

    // ✅ Send the profile EXACTLY as it is stored - don't restructure it
    const payload = {
      profile: profile, // Use the profile exactly as stored
      resume: profile.uploadedResumeText || "",
      job: job
    };

    console.log("Match score payload:", payload); // Debug log

    try {
      const res = await fetch("http://localhost:8000/match-score", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const data = await res.json();
      console.log("Match score response:", data); // Debug log

      // ✅ Safely structure the result with fallbacks
      const safeResult = {
        overall_score: typeof data.overall_score === 'number' ? data.overall_score : 0,
        section_scores: {
          skills: typeof data.section_scores?.skills === 'number' ? data.section_scores.skills : 0,
          experience: typeof data.section_scores?.experience === 'number' ? data.section_scores.experience : 0,
          education: typeof data.section_scores?.education === 'number' ? data.section_scores.education : 0,
        },
        missing: {
          skills: Array.isArray(data.missing?.skills) ? data.missing.skills : [],
          experience_keywords: Array.isArray(data.missing?.experience_keywords) ? data.missing.experience_keywords : [],
          education_keywords: Array.isArray(data.missing?.education_keywords) ? data.missing.education_keywords : [],
        },
        feedback: Array.isArray(data.feedback) ? data.feedback : ["No feedback available"],
        // ✅ Include LLM analysis if available
        llm_analysis: data.llm_analysis || null,
        metadata: data.metadata || {}
      };

      setResult(safeResult);
      
      // Cache the results (but DON'T save back to profile DB)
      localStorage.setItem("lastMatchScore", JSON.stringify(safeResult));
      localStorage.setItem("lastAnalyzedJob", JSON.stringify(job));
      
      setStatusMessage("");
    } catch (error) {
      console.error("Match score failed:", error);
      setStatusMessage(`❌ Failed to compute match score: ${error.message}`);
      
      // ✅ Provide fallback result
      setResult({
        overall_score: 0,
        section_scores: { skills: 0, experience: 0, education: 0 },
        missing: { skills: [], experience_keywords: [], education_keywords: [] },
        feedback: ["Error occurred during analysis. Please try again."],
        llm_analysis: null,
        metadata: { error: error.message }
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitFeedback = async () => {
    if (!result) {
      setStatusMessage("❌ No result available to submit feedback for.");
      return;
    }

    if (!userFeedback.trim()) {
      setStatusMessage("❌ Please enter some feedback.");
      return;
    }

    const payload = {
      profile_snapshot: JSON.stringify(profile),
      job_snapshot: JSON.stringify(job),
      overall_score: result.overall_score,
      skills_score: result.section_scores?.skills ?? 0,
      experience_score: result.section_scores?.experience ?? 0,
      education_score: result.section_scores?.education ?? 0,
      feedback_text: userFeedback,
    };

    try {
      const res = await fetch("http://localhost:8000/submit-feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      setStatusMessage(data.status === "success"
        ? "✅ Feedback submitted successfully!"
        : "❌ Failed to submit feedback.");
      
      if (data.status === "success") {
        setUserFeedback("");
      }
    } catch (err) {
      console.error("Feedback submission failed:", err);
      setStatusMessage("❌ Feedback submission failed.");
    }
  };

  // ✅ Show loading state
  if (profile === null) {
    return (
      <ThemeProvider theme={ClassyTheme}>
        <Stack
          styles={{
            root: {
              background: ClassyTheme.palette.neutralLighter,
              padding: 32,
              maxWidth: 880,
              margin: "auto",
              borderRadius: 12,
              minHeight: "400px",
              justifyContent: "center",
              alignItems: "center"
            },
          }}
        >
          <Text variant="xLarge">Loading profile...</Text>
          {statusMessage && (
            <Text variant="medium" styles={{ root: { marginTop: 16, color: "#d13438" } }}>
              {statusMessage}
            </Text>
          )}
        </Stack>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={ClassyTheme}>
      <Stack
        styles={{
          root: {
            background: ClassyTheme.palette.neutralLighter,
            padding: 32,
            maxWidth: 880,
            margin: "auto",
            borderRadius: 12,
            color: ClassyTheme.palette.black,
          },
        }}
        tokens={{ childrenGap: 20 }}
      >
        <Text
          variant="xxLarge"
          styles={{ root: { color: ClassyTheme.palette.themePrimary, textAlign: "center" } }}
        >
          Match Score Analysis
        </Text>

        <Stack horizontal horizontalAlign="center" tokens={{ childrenGap: 12 }}>
          <PrimaryButton 
            text={loading ? "Computing..." : "Recompute Score"} 
            onClick={runMatchScore}
            disabled={loading}
          />
          <DefaultButton text="Back to Profile" onClick={() => navigate("/")} />
        </Stack>

        {statusMessage && (
          <MessageBar
            messageBarType={statusMessage.includes("❌") ? MessageBarType.error : 
                           statusMessage.includes("🔄") ? MessageBarType.info : 
                           MessageBarType.success}
            isMultiline={false}
            onDismiss={() => setStatusMessage("")}
          >
            {statusMessage}
          </MessageBar>
        )}

        {/* ✅ Show current profile info for debugging */}
        <Stack
          styles={{
            root: {
              background: "#e8f4fd",
              padding: 16,
              borderRadius: 8,
              border: `1px solid ${ClassyTheme.palette.themeLighter}`,
            },
          }}
          tokens={{ childrenGap: 8 }}
        >
          <Text variant="large" styles={{ root: { color: ClassyTheme.palette.themePrimary } }}>
            Profile: {profile?.fullName || "No name set"}
          </Text>
          <Text variant="medium">
            Skills: {Array.isArray(profile?.skills) ? profile.skills.length : 0} | 
            Experience: {Array.isArray(profile?.experience) ? profile.experience.length : 0} | 
            Education: {Array.isArray(profile?.education) ? profile.education.length : 0}
          </Text>
          {job.title && (
            <Text variant="medium">
              Analyzing for: {job.title} at {job.company || "Unknown Company"}
            </Text>
          )}
        </Stack>

        {result && (
          <Stack
            styles={{
              root: {
                background: "#f7f7f9",
                padding: 24,
                borderRadius: 10,
                boxShadow: "0 0 8px rgba(0,0,0,0.1)",
              },
            }}
            tokens={{ childrenGap: 20 }}
          >
            <Stack tokens={{ childrenGap: 8 }}>
              <Text variant="xLarge" styles={{ root: { color: ClassyTheme.palette.themePrimary } }}>
                Overall Match Score
              </Text>
              <Text variant="mega" styles={{ 
                root: { 
                  color: result.overall_score >= 70 ? "#107c10" : 
                         result.overall_score >= 50 ? "#ff8c00" : "#d13438",
                  fontWeight: 600
                }
              }}>
                {Math.round(result.overall_score)}%
              </Text>
            </Stack>

            <Separator />

            <Stack tokens={{ childrenGap: 8 }}>
              <Text variant="large" styles={{ root: { color: ClassyTheme.palette.themeTertiary } }}>
                Section-wise Breakdown
              </Text>
              {result.section_scores &&
                Object.entries(result.section_scores).map(([section, score]) => (
                  <Stack key={section} horizontal horizontalAlign="space-between">
                    <Text>
                      <strong style={{ textTransform: "capitalize" }}>{section}</strong>
                    </Text>
                    <Text styles={{ 
                      root: { 
                        color: score >= 70 ? "#107c10" : 
                               score >= 50 ? "#ff8c00" : "#d13438",
                        fontWeight: 600
                      }
                    }}>
                      {Math.round(score)}%
                    </Text>
                  </Stack>
                ))}
            </Stack>

            <Separator />

            <Stack tokens={{ childrenGap: 8 }}>
              <Text variant="large" styles={{ root: { color: ClassyTheme.palette.themeTertiary } }}>
                Missing Keywords
              </Text>
              {result.missing &&
                Object.entries(result.missing).map(([section, items]) => (
                  <Stack key={section} tokens={{ childrenGap: 4 }}>
                    <Text>
                      <strong style={{ textTransform: "capitalize" }}>
                        {section.replace('_keywords', '')}:
                      </strong>
                    </Text>
                    <Text styles={{ root: { marginLeft: 16, fontStyle: 'italic' } }}>
                      {Array.isArray(items) && items.length > 0 ? items.join(", ") : "None identified"}
                    </Text>
                  </Stack>
                ))}
            </Stack>

               {Array.isArray(result.feedback) && result.feedback.length > 0 && (
              <Stack tokens={{ childrenGap: 10 }}>
                <Separator />
                <Text variant="large" styles={{ root: { color: ClassyTheme.palette.themeTertiary } }}>
                  AI Suggestions
                </Text>
                <Stack
                  styles={{
                    root: {
                      backgroundColor: "#f0f0f5",
                      padding: 16,
                      borderRadius: 8,
                      borderLeft: `4px solid ${ClassyTheme.palette.themeSecondary}`,
                    },
                  }}
                  tokens={{ childrenGap: 6 }}
                >
                  {result.feedback.map((line, idx) => {
                    const trimmed = line.trim();
                    if (!trimmed) return null;
                    const isHeader = /(strength|gap|resume|overall|recommendation)/i.test(trimmed);
                    return isHeader ? (
                      <Text key={idx} styles={{ root: { fontWeight: 600, marginTop: 12 } }}>
                        {trimmed}
                      </Text>
                    ) : (
                      <Text key={idx}>{trimmed}</Text>
                    );
                  })}
                </Stack>
              </Stack>
            )}

            <Stack tokens={{ childrenGap: 10 }}>
              <Text variant="mediumPlus" styles={{ root: { color: ClassyTheme.palette.themeTertiary } }}>
                Your Feedback
              </Text>
              <TextField
                multiline
                rows={4}
                placeholder="What could be improved?"
                value={userFeedback}
                onChange={(e, val) => setUserFeedback(val)}
              />
              <PrimaryButton text="Submit Feedback" onClick={handleSubmitFeedback} />
            </Stack>
          </Stack>
        )}
      </Stack>
    </ThemeProvider>
  );
}