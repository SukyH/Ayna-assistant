import React, { useState, useEffect } from 'react';
import {
  Stack,
  TextField,
  PrimaryButton,
  DefaultButton,
  Label,
  IconButton,
  ThemeProvider,
  Text,
} from '@fluentui/react';
import { useNavigate } from 'react-router-dom';
import {
  getProfileFromDB,
  saveProfileToDB,
  saveResumeToDB,
} from '../Database/db';
import { ClassyTheme } from '../themes/ClassyTheme';

const defaultProfile = {
  fullName: '', email: '', phone: '', location: '',
  linkedin: '', github: '', portfolio: '', summary: '',
  education: [], experience: [], projects: [], skills: [], licenses: []
};

const ProfileBuilder = () => {
  const [profile, setProfile] = useState(defaultProfile);
  const [rawText, setRawText] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    (async () => {
      const stored = await getProfileFromDB();
      if (stored) setProfile(stored);
    })();
  }, []);

  const handleChange = (e, newValue) => {
    const { name } = e.target;
    setProfile(prev => ({ ...prev, [name]: newValue }));
  };

  const handleSkillsChange = (_, newValue) => {
    setProfile(prev => ({ ...prev, skills: newValue.split(',').map(s => s.trim()) }));
  };

  const handleItemChange = (section, index, field, value) => {
    const updated = [...profile[section]];
    updated[index][field] = value;
    setProfile(prev => ({ ...prev, [section]: updated }));
  };

  const deleteItem = (section, index) => {
    const updated = [...profile[section]];
    updated.splice(index, 1);
    setProfile(prev => ({ ...prev, [section]: updated }));
  };

  const addItem = (section, template) => {
    setProfile(prev => ({ ...prev, [section]: [...prev[section], template] }));
  };

  const handleSave = async () => {
    await saveProfileToDB(profile);
    alert('✅ Profile saved!');
  };

  const handleResumeUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const buffer = await file.arrayBuffer();
    await saveResumeToDB({ name: file.name, type: file.type, buffer });
    alert("📄 Resume uploaded!");
  };

  const handleEnrichProfile = async () => {
    try {
      const response = await fetch("http://localhost:8000/enrich-profile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profile),
      });

      const data = await response.json();
      if (data?.enriched) {
        setProfile(data.enriched);
        alert("✅ Profile enriched!");
      } else {
        alert("❌ Failed to enrich profile.");
      }
    } catch (err) {
      console.error("Enrich error:", err);
      alert("⚠️ Error occurred during enrichment.");
    }
  };

  const handlePasteProfile = async () => {
    try {
      const response = await fetch("http://localhost:8000/enrich-text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: rawText }),
      });

      const data = await response.json();
      if (data.enriched && typeof data.enriched === "object") {
        const enriched = data.enriched;

        const merged = {
          ...profile,
          ...Object.fromEntries(
            Object.entries(enriched).map(([key, value]) => {
              if (Array.isArray(value)) {
                const existing = Array.isArray(profile[key]) ? profile[key] : [];
                const newItems = value.filter(
                  (item) =>
                    !existing.some((ex) =>
                      JSON.stringify(ex).toLowerCase() === JSON.stringify(item).toLowerCase()
                    )
                );
                return [key, [...existing, ...newItems]];
              }
              return [key, profile[key] ? profile[key] : value];
            })
          ),
        };

        setProfile(merged);
        alert("✅ Profile updated from pasted text without overwriting existing fields!");
      } else {
        alert("❌ Failed to enrich profile.");
      }
    } catch (err) {
      console.error("Paste error:", err);
      alert(`⚠️ An error occurred while enriching profile: ${err.message || err}`);
    }
  };

  const renderSection = (title, section, template) => (
    <Stack
      key={section}
      tokens={{ childrenGap: 12 }}
      styles={{
        root: {
          backgroundColor: ClassyTheme.palette.themeLighter,
          padding: 16,
          borderRadius: 8,
          marginBottom: 24,
        },
      }}
    >
      <Text variant="xLarge" styles={{ root: { color: ClassyTheme.palette.themeDark } }}>{title}</Text>
      {profile[section].map((item, index) => (
        <Stack key={index} tokens={{ childrenGap: 8 }}>
          {Object.entries(item).map(([key, value]) => (
            <TextField
              key={key}
              label={key}
              value={value}
              onChange={(_, val) => handleItemChange(section, index, key, val)}
            />
          ))}
          <IconButton iconProps={{ iconName: 'Delete' }} title="Delete" onClick={() => deleteItem(section, index)} />
        </Stack>
      ))}
      <PrimaryButton
        text={`Add ${title}`}
        onClick={() => addItem(section, template)}
        styles={{ root: { width: 'fit-content', marginTop: 8 } }}
      />
    </Stack>
  );

  return (
    <ThemeProvider theme={ClassyTheme}>
      <Stack
        styles={{ root: { background: ClassyTheme.palette.white, minHeight: '100vh', padding: 24 } }}
        tokens={{ childrenGap: 24 }}
      >
        <Text variant="xxLarge" styles={{ root: { textAlign: 'center', color: ClassyTheme.palette.themePrimary } }}>
          Smart Job Assistant Profile Builder
        </Text>

        {/* Personal Info Section */}
        <Stack tokens={{ childrenGap: 16 }}>
          <TextField label="Full Name" name="fullName" value={profile.fullName} onChange={handleChange} />
          <TextField label="Email" name="email" value={profile.email} onChange={handleChange} />
          <TextField label="Phone" name="phone" value={profile.phone} onChange={handleChange} />
          <TextField label="Location" name="location" value={profile.location} onChange={handleChange} />
          <TextField label="LinkedIn" name="linkedin" value={profile.linkedin} onChange={handleChange} />
          <TextField label="GitHub" name="github" value={profile.github} onChange={handleChange} />
          <TextField label="Portfolio" name="portfolio" value={profile.portfolio} onChange={handleChange} />
          <TextField label="Summary" multiline rows={3} name="summary" value={profile.summary} onChange={handleChange} />
          <TextField label="Skills (comma-separated)" value={profile.skills.join(',')} onChange={handleSkillsChange} />
        </Stack>

        {/* Dynamic Sections */}
        {renderSection("Education", "education", {
          school: "", degree: "", field: "", startDate: "", endDate: "", gpa: ""
        })}
        {renderSection("Experience", "experience", {
          company: "", position: "", startDate: "", endDate: "", description: ""
        })}
        {renderSection("Projects", "projects", {
          name: "", techStack: "", description: "", link: ""
        })}
        {renderSection("Licenses & Certifications", "licenses", {
          title: "", description: "", issueDate: "", expiryDate: ""
        })}

        {/* Paste LinkedIn Profile Section */}
        <Stack tokens={{ childrenGap: 8 }}>
          <Label>Paste LinkedIn or other text (structured or messy):</Label>
          <TextField
            multiline
            rows={4}
            placeholder="Paste any content from LinkedIn, resume, or your experience here..."
            value={rawText}
            onChange={(_, val) => setRawText(val)}
          />
        </Stack>

        <Stack horizontal tokens={{ childrenGap: 16 }} horizontalAlign="center">
          <PrimaryButton
            text="Paste LinkedIn Profile"
            onClick={handlePasteProfile}
            styles={{
              root: { background: ClassyTheme.palette.themePrimary, color: "white" },
              rootHovered: { background: ClassyTheme.palette.themeSecondary }
            }}
          />
          <PrimaryButton
            text="Enrich Profile"
            onClick={handleEnrichProfile}
            styles={{
              root: { background: ClassyTheme.palette.themePrimary, color: "white" },
              rootHovered: { background: ClassyTheme.palette.themeSecondary }
            }}
          />
        </Stack>

        {/* Resume Upload */}
        <Stack tokens={{ childrenGap: 12 }}>
          <Label>Upload Resume</Label>
          <input type="file" accept=".pdf,.doc,.docx" onChange={handleResumeUpload} />
        </Stack>

        {/* Save + Back */}
        <Stack horizontal tokens={{ childrenGap: 16 }} horizontalAlign="center">
          <PrimaryButton text="Save Profile" onClick={handleSave} />
          <DefaultButton text="Back to Profile" onClick={() => navigate("/")} />
        </Stack>
      </Stack>
    </ThemeProvider>
  );
};

export default ProfileBuilder;
