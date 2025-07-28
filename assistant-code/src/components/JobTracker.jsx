import React, { useState, useEffect } from "react";
import {
  Stack,
  Text,
  TextField,
  Dropdown,
  IDropdownOption,
  DefaultButton,
  PrimaryButton,
  IconButton,
  DateTimePicker,
  ThemeProvider,
} from "@fluentui/react";
import { useNavigate } from "react-router-dom";
import { ClassyTheme } from "../themes/ClassyTheme";

const JobTracker = () => {
  const [jobs, setJobs] = useState([]);
  const [form, setForm] = useState({
    title: "",
    company: "",
    status: "Saved",
    url: "",
    reminder_datetime: "",
    feedback: "",
  });

  const [editJobId, setEditJobId] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [filterStatus, setFilterStatus] = useState("All");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();
  const API_URL = "http://localhost:8000";

  const statusOptions = [
    { key: "Saved", text: "📌 Saved" },
    { key: "Applied", text: "📤 Applied" },
    { key: "Interviewed", text: "🎯 Interviewed" },
    { key: "Offer", text: "🎉 Offer" },
    { key: "Rejected", text: "❌ Rejected" },
  ];

  const statusColors = {
    Saved: ClassyTheme.palette.themeTertiary,
    Applied: "#a0d3f5",
    Interviewed: "#ffe08a",
    Offer: "#c1f0c1",
    Rejected: "#f7b2ad",
  };

  const statusIcons = {
    Saved: "📌",
    Applied: "📤",
    Interviewed: "🎯",
    Offer: "🎉",
    Rejected: "❌",
  };

  useEffect(() => {
    fetchJobs();
    if ("Notification" in window && Notification.permission !== "granted") {
      Notification.requestPermission();
    }
  }, []);

  const fetchJobs = async () => {
    try {
      const res = await fetch(`${API_URL}/job-tracker/all`);
      const data = await res.json();
      setJobs(data);
      scheduleReminders(data);
    } catch (err) {
      console.error("Failed to load jobs:", err);
    }
  };

  const handleChange = (e, item) => {
    const name = e.target?.name || item?.key;
    const value = e.target?.value || item?.text;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async () => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    const reminderDate = form.reminder_datetime ? new Date(form.reminder_datetime).toISOString() : null;

    const payload = {
      title: form.title || "Untitled",
      company: form.company || "Unknown",
      status: form.status,
      url: form.url,
      notes: form.feedback,
      feedback: form.feedback,
      reminder_date: reminderDate,
    };

    try {
      const res = await fetch(`${API_URL}/job-tracker/add`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const newJob = await res.json();
      setJobs([newJob, ...jobs]);
      setForm({ title: "", company: "", status: "Saved", url: "", reminder_datetime: "", feedback: "" });
      if (reminderDate) triggerReminder(reminderDate, newJob.title);
    } catch (err) {
      console.error("Failed to add job:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const scheduleReminders = (jobs) => {
    jobs.forEach((job) => {
      if (job.reminder_date) {
        triggerReminder(job.reminder_date, job.title);
      }
    });
  };
  

  const triggerReminder = (date, title) => {
    const timeUntil = new Date(date).getTime() - Date.now();
    if (timeUntil <= 0) return;
    setTimeout(() => {
      new Notification("Job Reminder", {
        body: `⏰ Follow up on ${title}`,
        icon: "/favicon.ico",
      });
    }, timeUntil);
  };

  const saveEdit = async (id) => {
    const payload = {
      ...editForm,
      reminder_date: editForm.reminder_datetime ? new Date(editForm.reminder_datetime).toISOString() : null,
    };

    try {
      const res = await fetch(`${API_URL}/job-tracker/update/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const updated = await res.json();
      setJobs(jobs.map((job) => (job.id === id ? updated : job)));
      setEditJobId(null);
      setEditForm({});
    } catch (err) {
      console.error("Update failed:", err);
    }
  };

  const startEditing = (job) => {
    setEditJobId(job.id);
    setEditForm({
      title: job.title,
      company: job.company,
      status: job.status,
      url: job.url,
      feedback: job.feedback,
      reminder_datetime: job.reminder_date ? new Date(job.reminder_date).toISOString().slice(0, 16) : "",
    });
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this job?")) return;
    await fetch(`${API_URL}/job-tracker/delete/${id}`, { method: "DELETE" });
    setJobs(jobs.filter((j) => j.id !== id));
  };

  const filteredJobs = filterStatus === "All" ? jobs : jobs.filter((job) => job.status === filterStatus);

  return (
    <ThemeProvider theme={ClassyTheme}>
      <Stack tokens={{ childrenGap: 24 }} styles={{ root: { padding: 32, backgroundColor: ClassyTheme.palette.white } }}>
        <Text variant="xxLarge" styles={{ root: { color: ClassyTheme.palette.themeDark } }}>📋 Job Application Tracker</Text>

        <Stack horizontal horizontalAlign="space-between">
          <Text variant="xLarge">➕ Add Job</Text>
          <DefaultButton text="View Profile" onClick={() => navigate("/")} />
        </Stack>

        <Stack horizontal tokens={{ childrenGap: 16 }}>
          <TextField label="Job Title" name="title" value={form.title} onChange={handleChange} />
          <TextField label="Company" name="company" value={form.company} onChange={handleChange} />
          <TextField label="Job URL" name="url" value={form.url} onChange={handleChange} />
        </Stack>

        <Stack horizontal tokens={{ childrenGap: 16 }}>
          <Dropdown
            label="Status"
            selectedKey={form.status}
            options={statusOptions}
            onChange={(e, option) => setForm({ ...form, status: option.key })}
          />
          <TextField
            label="Reminder (Local Time)"
            type="datetime-local"
            name="reminder_datetime"
            value={form.reminder_datetime}
            onChange={handleChange}
          />
        </Stack>

        <TextField
          label="Feedback / Notes"
          name="feedback"
          multiline
          rows={3}
          value={form.feedback}
          onChange={handleChange}
        />

        <PrimaryButton
          text={isSubmitting ? "Adding..." : "Add Job"}
          onClick={handleSubmit}
          disabled={isSubmitting}
        />

        <Dropdown
          label="Filter by Status"
          options={[{ key: "All", text: "All" }, ...statusOptions]}
          selectedKey={filterStatus}
          onChange={(e, option) => setFilterStatus(option.key)}
        />

        <Stack tokens={{ childrenGap: 16 }}>
          {filteredJobs.map((job) => (
            <Stack
              key={job.id}
              tokens={{ childrenGap: 8 }}
              styles={{
                root: {
                  padding: 16,
                  borderRadius: 6,
                  border: `1px solid ${ClassyTheme.palette.neutralLight}`,
                  backgroundColor: ClassyTheme.palette.neutralLighterAlt,
                },
              }}
            >
              {editJobId === job.id ? (
                <>
                  <Stack horizontal tokens={{ childrenGap: 12 }}>
                    <TextField label="Job Title" name="title" value={editForm.title} onChange={(e, val) => setEditForm({ ...editForm, title: val })} />
                    <TextField label="Company" name="company" value={editForm.company} onChange={(e, val) => setEditForm({ ...editForm, company: val })} />
                    <Dropdown
                      label="Status"
                      selectedKey={editForm.status}
                      options={statusOptions}
                      onChange={(e, option) => setEditForm({ ...editForm, status: option.key })}
                    />
                    <TextField
                      label="Reminder"
                      type="datetime-local"
                      value={editForm.reminder_datetime}
                      onChange={(e, val) => setEditForm({ ...editForm, reminder_datetime: val })}
                    />
                  </Stack>
                  <TextField
                    label="Feedback"
                    multiline
                    rows={2}
                    value={editForm.feedback}
                    onChange={(e, val) => setEditForm({ ...editForm, feedback: val })}
                  />
                  <Stack horizontal tokens={{ childrenGap: 8 }}>
                    <PrimaryButton text="Save" onClick={() => saveEdit(job.id)} />
                    <DefaultButton text="Cancel" onClick={() => setEditJobId(null)} />
                  </Stack>
                </>
              ) : (
                <>
                  <Text variant="large">
                    {statusIcons[job.status]} <b>{job.title}</b> at <b>{job.company}</b>
                  </Text>
                  <Text variant="small">Reminder: {job.reminder_date ? new Date(job.reminder_date).toLocaleString() : "None"}</Text>
                  {job.feedback && <Text variant="small">📝 {job.feedback}</Text>}
                  <Stack horizontal tokens={{ childrenGap: 12 }}>
                    <DefaultButton text="Edit" onClick={() => startEditing(job)} />
                    <DefaultButton text="Delete" onClick={() => handleDelete(job.id)} />
                    {job.url && (
                      <DefaultButton
                        text="View Job Post"
                        onClick={() => window.open(job.url, "_blank")}
                      />
                    )}
                  </Stack>
                </>
              )}
            </Stack>
          ))}
        </Stack>
      </Stack>
    </ThemeProvider>
  );
};

export default JobTracker;
