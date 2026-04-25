"use client";

import { ThemeInit } from "@/components/ThemeInit";
import { getApiBase } from "@/lib/apiBase";
import { getUser, saveUser, UserProfile } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

const STATES = [
  "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh","Goa","Gujarat",
  "Haryana","Himachal Pradesh","Jharkhand","Karnataka","Kerala","Madhya Pradesh",
  "Maharashtra","Manipur","Meghalaya","Mizoram","Nagaland","Odisha","Punjab",
  "Rajasthan","Sikkim","Tamil Nadu","Telangana","Tripura","Uttar Pradesh",
  "Uttarakhand","West Bengal","Delhi","Jammu & Kashmir","Ladakh","Chandigarh",
  "Puducherry","Lakshadweep","Andaman & Nicobar","Dadra & Nagar Haveli",
];

const GENDERS = ["Male","Female","Transgender","Prefer not to say"];
const CASTES  = ["General","OBC","SC","ST","EWS","Prefer not to say"];
const OCCUPATIONS = [
  "Student","Farmer","Self-employed","Salaried (Govt)","Salaried (Private)",
  "Daily Wage Worker","Construction Worker","Homemaker","Unemployed","Other",
];
const INCOMES = [
  "Below ₹1 lakh","₹1-3 lakh","₹3-5 lakh","₹5-10 lakh","Above ₹10 lakh","Prefer not to say",
];
const EDUCATIONS = [
  "No formal education","Primary (up to Class 5)","Secondary (Class 10)",
  "Higher Secondary (Class 12)","Graduate","Post-graduate","Prefer not to say",
];

interface Scheme {
  name: string;
  slug: string;
  state: string;
  categories: string;
  benefits: string;
  eligibility: string;
}

export default function OnboardingPage() {
  const router = useRouter();
  const [user, setUser] = useState<UserProfile | null>(null);
  const [step, setStep] = useState(0); // 0 = form, 1 = schemes
  const [form, setForm] = useState<Partial<UserProfile>>({});
  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [loading, setLoading] = useState(false);
  const base = getApiBase();

  useEffect(() => {
    const u = getUser();
    if (!u) { router.push("/login/"); return; }
    if (u.onboarded) { router.push("/chat/"); return; }
    setUser(u);
    setForm({ gender: u.gender, state: u.state });
  }, [router]);

  const Field = ({
    label, name, type = "text", options, placeholder,
  }: {
    label: string; name: keyof UserProfile;
    type?: string; options?: string[]; placeholder?: string;
  }) => (
    <div>
      <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--fg2)" }}>
        {label}
      </label>
      {options ? (
        <select
          className="ns-input"
          value={(form[name] as string) || ""}
          onChange={(e) => setForm((f) => ({ ...f, [name]: e.target.value }))}
        >
          <option value="">Select…</option>
          {options.map((o) => <option key={o}>{o}</option>)}
        </select>
      ) : (
        <input
          type={type}
          placeholder={placeholder}
          className="ns-input"
          value={(form[name] as string | number | undefined) ?? ""}
          onChange={(e) => setForm((f) => ({ ...f, [name]: type === "number" ? Number(e.target.value) : e.target.value }))}
        />
      )}
    </div>
  );

  const submit = async () => {
    setLoading(true);
    try {
      const r = await fetch(`${base}/api/recommend-schemes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: user?.name,
          age: form.age,
          gender: form.gender,
          state: form.state,
          locality: form.locality,
          caste: form.caste,
          occupation: form.occupation,
          annual_income: form.annual_income,
          education: form.education,
        }),
      });
      const data = await r.json();
      setSchemes(data.schemes || []);
    } catch {
      setSchemes([]);
    } finally {
      setLoading(false);
      setStep(1);
      const updated = { ...user!, ...form, onboarded: true };
      saveUser(updated);
    }
  };

  const goToChat = () => router.push("/chat/");

  if (!user) return null;

  return (
    <>
      <ThemeInit />
      <div className="flex min-h-dvh items-start justify-center px-4 py-10" style={{ background: "var(--bg)" }}>
        <div className="w-full max-w-2xl">

          {step === 0 && (
            <div className="glass px-8 py-10 shadow-2xl">
              <div className="mb-8 text-center">
                {user.picture && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={user.picture} alt="" className="mx-auto mb-3 h-16 w-16 rounded-full" />
                )}
                <h1 className="text-2xl font-black">Welcome, {user.name?.split(" ")[0]}!</h1>
                <p className="mt-1 text-sm" style={{ color: "var(--fg2)" }}>
                  Tell us a bit about yourself so we can show relevant government schemes.
                </p>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Age" name="age" type="number" placeholder="e.g. 28" />
                <Field label="Gender" name="gender" options={GENDERS} />
                <Field label="State" name="state" options={STATES} />
                <Field label="District / Locality" name="locality" placeholder="e.g. Pune, Karol Bagh" />
                <Field label="Caste Category" name="caste" options={CASTES} />
                <Field label="Occupation" name="occupation" options={OCCUPATIONS} />
                <Field label="Annual Income" name="annual_income" options={INCOMES} />
                <Field label="Education" name="education" options={EDUCATIONS} />
              </div>

              <div className="mt-8 flex gap-3">
                <button
                  className="btn-accent flex-1 py-3 text-sm"
                  onClick={submit}
                  disabled={loading}
                >
                  {loading ? "Matching schemes…" : "Find my schemes →"}
                </button>
                <button className="btn-ghost px-5 py-3 text-sm" onClick={goToChat}>
                  Skip
                </button>
              </div>
            </div>
          )}

          {step === 1 && (
            <div>
              <div className="mb-6 text-center">
                <h2 className="text-2xl font-black">Your matched schemes</h2>
                <p className="mt-1 text-sm" style={{ color: "var(--fg2)" }}>
                  Based on your profile — {schemes.length} scheme{schemes.length !== 1 ? "s" : ""} found.
                </p>
              </div>

              {schemes.length === 0 ? (
                <p className="text-center text-sm" style={{ color: "var(--fg2)" }}>
                  No matching schemes found for your profile. Try asking the assistant directly!
                </p>
              ) : (
                <div className="space-y-3">
                  {schemes.map((s, i) => (
                    <div key={i} className="feature-card">
                      <div className="flex items-start gap-3">
                        <span
                          className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-xs font-bold text-white"
                          style={{ background: "var(--user-grad)" }}
                        >
                          {i + 1}
                        </span>
                        <div>
                          <p className="font-bold text-sm">{s.name}</p>
                          {s.state && (
                            <p className="text-xs mt-0.5" style={{ color: "var(--accent)" }}>{s.state} · {s.categories}</p>
                          )}
                          {s.benefits && (
                            <p className="text-xs mt-1" style={{ color: "var(--fg2)" }}>
                              {s.benefits.slice(0, 200)}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <button className="btn-accent mt-8 w-full py-3 text-sm" onClick={goToChat}>
                Continue to assistant →
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
