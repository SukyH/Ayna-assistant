import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ThemeProvider,
  Stack,
  Text,
  DefaultButton,
  PrimaryButton,
  Link,
} from "@fluentui/react";
import {
  getProfileFromDB,
  getResumeFromDB,
  deleteResumeFromDB,
} from "../Database/db";
import { ClassyTheme } from "../themes/ClassyTheme";

const ProfileView = () => {
  const [profile, setProfile] = useState(null);
  const [resume, setResume] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    (async () => {
      const savedProfile = await getProfileFromDB();
      setProfile(savedProfile);
      const savedResume = await getResumeFromDB();
      if (savedResume?.buffer) {
        const blob = new Blob([savedResume.buffer], { type: savedResume.type });
        const resumeURL = URL.createObjectURL(blob);
        setResume({ name: savedResume.name, url: resumeURL });
      } else {
        setResume(null);
      }
    })();
  }, []);

  const sectionCard = (title, content) => (
    <Stack
      tokens={{ childrenGap: 12 }}
      styles={{
        root: {
          background: "#ffffff",
          color: "#000000",
          padding: 24,
          borderRadius: 10,
          border: `1px solid ${ClassyTheme.palette.themeTertiary}`,
          boxShadow: `0 2px 8px rgba(0,0,0,0.1)`,
        },
      }}
    >
      <Text
        variant="xLarge"
        styles={{ root: { color: ClassyTheme.palette.themePrimary, fontWeight: 600 } }}
      >
        {title}
      </Text>
      {content}
    </Stack>
  );

  return (
    <ThemeProvider theme={ClassyTheme}>
      <Stack
        tokens={{ childrenGap: 32 }}
        styles={{
          root: {
            background: "#f7f7f7",
            minHeight: "100vh",
            padding: "48px 32px",
            maxWidth: 1100,
            margin: "auto",
          },
        }}
      >
        <Text
          variant="xxLarge"
          styles={{ root: { textAlign: "center", color: ClassyTheme.palette.themePrimary } }}
        >
          Current Profile
        </Text>

        {profile ? (
          <>
            {sectionCard("Basic Info", (
              <Stack tokens={{ childrenGap: 6 }}>
                <Text><strong>Name:</strong> {profile.fullName}</Text>
                <Text><strong>Location:</strong> {profile.location}</Text>
                <Text><strong>Summary:</strong> {profile.summary}</Text>
                <Text><strong>Skills:</strong> {profile.skills?.join(", ")}</Text>

                {/* ✅ Added Social Links */}
                {profile.linkedin && (
                  <Text><strong>LinkedIn:</strong> <Link href={profile.linkedin} target="_blank">{profile.linkedin}</Link></Text>
                )}
                {profile.github && (
                  <Text><strong>GitHub:</strong> <Link href={profile.github} target="_blank">{profile.github}</Link></Text>
                )}
                {profile.portfolio && (
                  <Text><strong>Portfolio:</strong> <Link href={profile.portfolio} target="_blank">{profile.portfolio}</Link></Text>
                )}
              </Stack>
            ))}

            {profile.education?.length > 0 &&
              sectionCard("Education", (
                <Stack tokens={{ childrenGap: 16 }}>
                  {profile.education.map((edu, idx) => (
                    <Stack key={idx}>
                      <Text variant="mediumPlus" styles={{ root: { fontWeight: 600 } }}>
                        {edu.degree} in {edu.field} @ {edu.school}
                      </Text>
                      <Text>{edu.startDate} – {edu.endDate} | GPA: {edu.gpa}</Text>
                    </Stack>
                  ))}
                </Stack>
              ))}

            {profile.experience?.length > 0 &&
              sectionCard("Experience", (
                <Stack tokens={{ childrenGap: 16 }}>
                  {profile.experience.map((exp, idx) => (
                    <Stack key={idx}>
                      <Text variant="mediumPlus" styles={{ root: { fontWeight: 600 } }}>
                        {exp.position} @ {exp.company}
                      </Text>
                      <Text>{exp.startDate} – {exp.endDate}</Text>
                      <Text>{exp.description}</Text>
                    </Stack>
                  ))}
                </Stack>
              ))}

            {profile.projects?.length > 0 &&
              sectionCard("Projects", (
                <Stack tokens={{ childrenGap: 16 }}>
                  {profile.projects.map((proj, idx) => (
                    <Stack key={idx}>
                      <Text variant="mediumPlus" styles={{ root: { fontWeight: 600 } }}>
                        {proj.name} ({proj.techStack})
                      </Text>
                      <Text>{proj.description}</Text>
                      {proj.link && (
                        <Link
                          href={proj.link}
                          target="_blank"
                          underline
                          styles={{ root: { color: ClassyTheme.palette.themeSecondary } }}
                        >
                          Project Link
                        </Link>
                      )}
                    </Stack>
                  ))}
                </Stack>
              ))}

            {profile.licenses?.length > 0 &&
              sectionCard("Licenses & Certifications", (
                <Stack tokens={{ childrenGap: 16 }}>
                  {profile.licenses.map((cert, idx) => (
                    <Stack key={idx}>
                      <Text variant="mediumPlus" styles={{ root: { fontWeight: 600 } }}>
                        {cert.title}
                      </Text>
                      <Text>{cert.description}</Text>
                      <Text>
                        Issued: {cert.issueDate}{" "}
                        {cert.expiryDate && `| Expires: ${cert.expiryDate}`}
                      </Text>
                    </Stack>
                  ))}
                </Stack>
              ))}
          </>
        ) : (
          <Text
            variant="large"
            styles={{ root: { color: ClassyTheme.palette.themeSecondary, textAlign: "center" } }}
          >
            No saved profile found.
          </Text>
        )}

        {sectionCard("Resume uploaded by user", (
          resume?.url ? (
            <Link
              href={resume.url}
              target="_blank"
              underline
              styles={{ root: { color: ClassyTheme.palette.themeSecondary } }}
            >
              {resume.name}
            </Link>
          ) : (
            <Text>No resume uploaded.</Text>
          )
        ))}

        <Stack horizontal wrap horizontalAlign="center" tokens={{ childrenGap: 20 }}>
          <PrimaryButton text="Edit Profile" onClick={() => navigate("/edit")} />
          <DefaultButton text="Analyze Job" onClick={() => navigate("/analyze-job")} />
          <DefaultButton text="View Job Tracker" onClick={() => navigate("/job-tracker")} />
          <DefaultButton
            text="Delete Resume"
            styles={{
              root: {
                background: "#c62828",
                color: "white",
              },
              rootHovered: {
                background: "#e53935",
              },
            }}
            onClick={async () => {
              await deleteResumeFromDB(resume?.url);
              if (resume?.url) URL.revokeObjectURL(resume.url);
              setResume(null);
              alert("Resume deleted.");
            }}
          />
        </Stack>
      </Stack>
    </ThemeProvider>
  );
};

export default ProfileView;
