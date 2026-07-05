---
id: nist-ai-rmf
type: Course
schema: pro-cert/nist/nist-ai-rmf
name: "NIST AI Risk Management Framework 1.0"
educationalLevel: professional
provider:
  name: "National Institute of Standards and Technology (NIST)"
  url: "https://www.nist.gov/artificial-intelligence"
competencyFramework: nist-ai-100-1
source: "NIST.AI.100-1.pdf — January 2023"
license: "Public Domain — U.S. Government work"

required_competencies:
  - id: govern-purpose
    label: "Purpose and role of GOVERN as cross-cutting function"
    weight: high
  - id: govern-1-subcategories
    label: "GOVERN 1.1–1.7 — Policies, processes, and practices"
    weight: high
  - id: govern-2-subcategories
    label: "GOVERN 2.1–2.3 — Accountability structures"
    weight: high
  - id: govern-3-subcategories
    label: "GOVERN 3.1–3.2 — Workforce diversity"
    weight: medium
  - id: govern-4-subcategories
    label: "GOVERN 4.1–4.3 — Risk culture"
    weight: high
  - id: govern-5-subcategories
    label: "GOVERN 5.1–5.2 — AI actor engagement"
    weight: medium
  - id: govern-6-subcategories
    label: "GOVERN 6.1–6.2 — Third-party and supply chain"
    weight: high
  - id: map-purpose
    label: "Purpose of MAP function"
    weight: high
  - id: map-1-subcategories
    label: "MAP 1.1–1.6 — Context established and understood"
    weight: high
  - id: map-2-subcategories
    label: "MAP 2.1–2.3 — Categorization of AI system"
    weight: high
  - id: map-3-subcategories
    label: "MAP 3.1–3.5 — Capabilities, benefits, and costs"
    weight: high
  - id: map-4-subcategories
    label: "MAP 4.1–4.2 — All components including third-party"
    weight: medium
  - id: map-5-subcategories
    label: "MAP 5.1–5.2 — Impacts to individuals, groups, society"
    weight: high
  - id: measure-purpose
    label: "Purpose and TEVV concept"
    weight: high
  - id: measure-1-subcategories
    label: "MEASURE 1.1–1.3 — Methods and metrics"
    weight: high
  - id: measure-2-subcategories
    label: "MEASURE 2.1–2.13 — Trustworthy characteristics evaluation"
    weight: high
  - id: measure-3-subcategories
    label: "MEASURE 3.1–3.3 — Risk tracking"
    weight: high
  - id: measure-4-subcategories
    label: "MEASURE 4.1–4.3 — Feedback about measurement efficacy"
    weight: medium
  - id: manage-purpose
    label: "Purpose and risk response options"
    weight: high
  - id: manage-1-subcategories
    label: "MANAGE 1.1–1.4 — Prioritize and respond"
    weight: high
  - id: manage-2-subcategories
    label: "MANAGE 2.1–2.4 — Strategies to maximize benefits"
    weight: high
  - id: manage-3-subcategories
    label: "MANAGE 3.1–3.2 — Third-party risk management"
    weight: medium
  - id: manage-4-subcategories
    label: "MANAGE 4.1–4.3 — Response, recovery, communication"
    weight: high
  - id: trust-overview
    label: "Overview of trustworthiness and socio-technical nature"
    weight: high
  - id: trust-seven-characteristics
    label: "All 7 trustworthiness characteristics with definitions"
    weight: high
  - id: trust-bias-categories
    label: "Three categories of AI bias"
    weight: medium
---

# GOVERN — Cross-Cutting Governance Function

<!-- competency: govern-purpose -->
## GOVERN — Overview {#key_takeaways .weight-high}

- **GOVERN** is a cross-cutting function — infused throughout MAP, MEASURE, and MANAGE; applies to ALL stages of AI risk management
- Cultivates a culture of risk management within organizations designing, developing, deploying, evaluating, or acquiring AI systems
- Strong governance can drive and enhance internal practices and norms to facilitate organizational risk culture
- GOVERN outlines processes, documents, and organizational schemes that anticipate, identify, and manage the risks a system can pose
- Incorporates processes to assess potential impacts and provides structure to align AI risk management with organizational values, principles, and strategic priorities
- Addresses full product lifecycle including legal issues concerning use of third-party software, hardware, and data
- Attention to governance is a **continual and intrinsic requirement** for effective AI risk management over an AI system's lifespan
- **6 categories, 19 subcategories total**: GOVERN 1 (7), GOVERN 2 (3), GOVERN 3 (2), GOVERN 4 (3), GOVERN 5 (2), GOVERN 6 (2)

<!-- competency: govern-1-subcategories -->
## GOVERN 1 — Policies, Processes, Procedures & Practices {#glossary .weight-high}

- **GOVERN 1.1** : Legal and regulatory requirements involving AI are understood, managed, and documented.
- **GOVERN 1.2** : The characteristics of trustworthy AI are integrated into organizational policies, processes, procedures, and practices.
- **GOVERN 1.3** : Processes, procedures, and practices are in place to determine the needed level of risk management activities based on the organization's risk tolerance.
- **GOVERN 1.4** : The risk management process and its outcomes are established through transparent policies, procedures, and other controls based on organizational risk priorities.
- **GOVERN 1.5** : Ongoing monitoring and periodic review of the risk management process and its outcomes are planned and organizational roles and responsibilities clearly defined, including determining the frequency of periodic review.
- **GOVERN 1.6** : Mechanisms are in place to inventory AI systems and are resourced according to organizational risk priorities.
- **GOVERN 1.7** : Processes and procedures are in place for decommissioning and phasing out AI systems safely and in a manner that does not increase risks or decrease the organization's trustworthiness.

<!-- competency: govern-2-subcategories -->
## GOVERN 2 — Accountability Structures {#glossary .weight-high}

- **GOVERN 2.1** : Roles and responsibilities and lines of communication related to mapping, measuring, and managing AI risks are documented and are clear to individuals and teams throughout the organization.
- **GOVERN 2.2** : The organization's personnel and partners receive AI risk management training to enable them to perform their duties and responsibilities consistent with related policies, procedures, duties, and agreements.
- **GOVERN 2.3** : Executive leadership of the organization takes responsibility for decisions about risks associated with AI system development and deployment.

<!-- competency: govern-3-subcategories -->
## GOVERN 3 — Workforce Diversity, Equity, Inclusion & Accessibility {#glossary .weight-medium}

- **GOVERN 3.1** : Decision-making related to mapping, measuring, and managing AI risks throughout the lifecycle is informed by a diverse team (e.g., diversity of demographics, disciplines, experience, expertise, and backgrounds).
- **GOVERN 3.2** : Policies and procedures are in place to define and differentiate roles and responsibilities for human-AI configurations and oversight of AI systems.

<!-- competency: govern-4-subcategories -->
## GOVERN 4 — Organizational Culture that Considers and Communicates AI Risk {#glossary .weight-high}

- **GOVERN 4.1** : Organizational policies and practices are in place to foster a critical thinking and safety-first mindset in the design, development, deployment, and uses of AI systems to minimize potential negative impacts.
- **GOVERN 4.2** : Organizational teams document the risks and potential impacts of the AI technology they design, develop, deploy, evaluate, and use, and they communicate about the impacts more broadly.
- **GOVERN 4.3** : Organizational practices are in place to enable AI testing, identification of incidents, and information sharing.

<!-- competency: govern-5-subcategories -->
## GOVERN 5 — Robust Engagement with Relevant AI Actors {#glossary .weight-medium}

- **GOVERN 5.1** : Organizational policies and practices are in place to collect, consider, prioritize, and integrate feedback from those external to the team that developed or deployed the AI system regarding the potential individual and societal impacts related to AI risks.
- **GOVERN 5.2** : Mechanisms are established to enable the team that developed or deployed AI systems to regularly incorporate adjudicated feedback from relevant AI actors into system design and implementation.

<!-- competency: govern-6-subcategories -->
## GOVERN 6 — Third-Party Software, Data & Supply Chain {#glossary .weight-high}

- **GOVERN 6.1** : Policies and procedures are in place that address AI risks associated with third-party entities, including risks of infringement of a third party's intellectual property or other rights.
- **GOVERN 6.2** : Contingency processes are in place to handle failures or incidents in third-party data or AI systems deemed to be high-risk.

---

# MAP — Establish Context and Identify Risks

<!-- competency: map-purpose -->
## MAP — Overview {#key_takeaways .weight-high}

- **MAP** establishes the context to frame risks related to an AI system — the interdependent activities of the AI lifecycle involve a diverse set of actors
- The MAP function enables negative risk prevention and informs decisions for processes such as model management, and initial go/no-go decisions about whether an AI solution is needed
- Outcomes in MAP are the basis for the **MEASURE** and **MANAGE** functions — without contextual knowledge, risk management is difficult to perform
- After completing MAP, organizations should have sufficient contextual knowledge about AI system impacts to inform an initial **go/no-go decision** about whether to design, develop, or deploy an AI system
- Implementation is enhanced by incorporating perspectives from a diverse internal team and engagement with those external to the team
- **5 categories, 18 subcategories total**: MAP 1 (6), MAP 2 (3), MAP 3 (5), MAP 4 (2), MAP 5 (2)

<!-- competency: map-1-subcategories -->
## MAP 1 — Context is Established and Understood {#glossary .weight-high}

- **MAP 1.1** : Intended purposes, potentially beneficial uses, context-specific laws, norms and expectations, and prospective settings in which the AI system will be deployed are understood and documented. Considerations include: the specific set or types of users along with their expectations; potential positive and negative impacts of system uses to individuals, communities, organizations, society, and the planet; assumptions and related limitations about AI system purposes, uses, and risks across the development or product AI lifecycle; and related TEVV and system metrics.
- **MAP 1.2** : Interdisciplinary AI actors, competencies, skills, and capacities for establishing context reflect demographic diversity and broad domain and user experience expertise, and their participation is documented. Opportunities for interdisciplinary collaboration are prioritized.
- **MAP 1.3** : The organization's mission and relevant goals for AI technology are understood and documented.
- **MAP 1.4** : The business value or context of business use has been clearly defined or — in the case of assessing existing AI systems — re-evaluated.
- **MAP 1.5** : Organizational risk tolerances are determined and documented.
- **MAP 1.6** : System requirements (e.g., "the system shall respect the privacy of its users") are elicited from and understood by relevant AI actors. Design decisions take socio-technical implications into account to address AI risks.

<!-- competency: map-2-subcategories -->
## MAP 2 — Categorization of the AI System {#glossary .weight-high}

- **MAP 2.1** : The specific tasks and methods used to implement the tasks that the AI system will support are defined (e.g., classifiers, generative models, recommenders).
- **MAP 2.2** : Information about the AI system's knowledge limits and how system output may be utilized and overseen by humans is documented. Documentation provides sufficient information to assist relevant AI actors when making decisions and taking subsequent actions.
- **MAP 2.3** : Scientific integrity and TEVV considerations are identified and documented, including those related to experimental design, data collection and selection (e.g., availability, representativeness, suitability), system trustworthiness, and construct validation.

<!-- competency: map-3-subcategories -->
## MAP 3 — Capabilities, Targeted Usage, Goals, and Expected Benefits & Costs {#glossary .weight-high}

- **MAP 3.1** : Potential benefits of intended AI system functionality and performance are examined and documented.
- **MAP 3.2** : Potential costs, including non-monetary costs, which result from expected or realized AI errors or system functionality and trustworthiness — as connected to organizational risk tolerance — are examined and documented.
- **MAP 3.3** : Targeted application scope is specified and documented based on the system's capability, established context, and AI system categorization.
- **MAP 3.4** : Processes for operator and practitioner proficiency with AI system performance and trustworthiness — and relevant technical standards and certifications — are defined, assessed, and documented.
- **MAP 3.5** : Processes for human oversight are defined, assessed, and documented in accordance with organizational policies from the GOVERN function.

<!-- competency: map-4-subcategories -->
## MAP 4 — Risks & Benefits Mapped for All Components {#glossary .weight-medium}

- **MAP 4.1** : Approaches for mapping AI technology and legal risks of its components — including the use of third-party data or software — are in place, followed, and documented, as are risks of infringement of a third party's intellectual property or other rights.
- **MAP 4.2** : Internal risk controls for components of the AI system, including third-party AI technologies, are identified and documented.

<!-- competency: map-5-subcategories -->
## MAP 5 — Impacts to Individuals, Groups, Communities, Organizations & Society {#glossary .weight-high}

- **MAP 5.1** : Likelihood and magnitude of each identified impact (both potentially beneficial and harmful) based on expected use, past uses of AI systems in similar contexts, public incident reports, feedback from those external to the team that developed or deployed the AI system, or other data are identified and documented.
- **MAP 5.2** : Practices and personnel for supporting regular engagement with relevant AI actors and integrating feedback about positive, negative, and unanticipated impacts are in place and documented.

---

# MEASURE — Analyze, Assess, Benchmark & Monitor

<!-- competency: measure-purpose -->
## MEASURE — Overview {#key_takeaways .weight-high}

- **MEASURE** employs quantitative, qualitative, or mixed-method tools, techniques, and methodologies to analyze, assess, benchmark, and monitor AI risk and related impacts
- Uses knowledge relevant to AI risks identified in the MAP function and informs the MANAGE function
- Measuring AI risks includes tracking metrics for trustworthy characteristics, social impact, and human-AI configurations
- Processes should include rigorous software testing and performance assessment methodologies with associated measures of uncertainty, comparisons to performance benchmarks, and formalized reporting and documentation of results
- TEVV = **Test, Evaluation, Verification, and Validation** — must be objective, repeatable, scalable; must adhere to scientific, legal, and ethical norms in an open and transparent process
- After MEASURE: objective, repeatable, or scalable TEVV processes including metrics, methods, and methodologies are in place, followed, and documented
- Measurement outcomes are utilized in the MANAGE function to assist risk **monitoring and response efforts**
- **4 categories, 22 subcategories total**: MEASURE 1 (3), MEASURE 2 (13), MEASURE 3 (3), MEASURE 4 (3)

<!-- competency: measure-1-subcategories -->
## MEASURE 1 — Appropriate Methods & Metrics Identified and Applied {#glossary .weight-high}

- **MEASURE 1.1** : Approaches and metrics for measurement of AI risks enumerated during the MAP function are selected for implementation starting with the most significant AI risks. The risks or trustworthiness characteristics that will not — or cannot — be measured are properly documented.
- **MEASURE 1.2** : Appropriateness of AI metrics and effectiveness of existing controls are regularly assessed and updated, including reports of errors and potential impacts on affected communities.
- **MEASURE 1.3** : Internal experts who did not serve as front-line developers for the system and/or independent assessors are involved in regular assessments and updates. Domain experts, users, AI actors external to the team that developed or deployed the AI system, and affected communities are consulted in support of assessments as necessary per organizational risk tolerance.

<!-- competency: measure-2-subcategories -->
## MEASURE 2 — AI Systems Evaluated for Trustworthy Characteristics {#glossary .weight-high}

- **MEASURE 2.1** : Test sets, metrics, and details about the tools used during TEVV are documented.
- **MEASURE 2.2** : Evaluations involving human subjects meet applicable requirements (including human subject protection) and are representative of the relevant population.
- **MEASURE 2.3** : AI system performance or assurance criteria are measured qualitatively or quantitatively and demonstrated for conditions similar to deployment setting(s). Measures are documented.
- **MEASURE 2.4** : The functionality and behavior of the AI system and its components — as identified in the MAP function — are monitored when in production.
- **MEASURE 2.5** : The AI system to be deployed is demonstrated to be valid and reliable. Limitations of the generalizability beyond the conditions under which the technology was developed are documented.
- **MEASURE 2.6** : The AI system is evaluated regularly for safety risks — as identified in the MAP function. The AI system to be deployed is demonstrated to be safe, its residual negative risk does not exceed the risk tolerance, and it can fail safely, particularly if made to operate beyond its knowledge limits. Safety metrics reflect system reliability and robustness, real-time monitoring, and response times for AI system failures.
- **MEASURE 2.7** : AI system security and resilience — as identified in the MAP function — are evaluated and documented.
- **MEASURE 2.8** : Risks associated with transparency and accountability — as identified in the MAP function — are examined and documented.
- **MEASURE 2.9** : The AI model is explained, validated, and documented, and AI system output is interpreted within its context — as identified in the MAP function — to inform responsible use and governance.
- **MEASURE 2.10** : Privacy risk of the AI system — as identified in the MAP function — is examined and documented.
- **MEASURE 2.11** : Fairness and bias — as identified in the MAP function — are evaluated and results are documented.
- **MEASURE 2.12** : Environmental impact and sustainability of AI model training and management activities — as identified in the MAP function — are assessed and documented.
- **MEASURE 2.13** : Effectiveness of the employed TEVV metrics and processes in the MEASURE function are evaluated and documented.

<!-- competency: measure-3-subcategories -->
## MEASURE 3 — Mechanisms for Tracking Identified AI Risks Over Time {#glossary .weight-high}

- **MEASURE 3.1** : Approaches, personnel, and documentation are in place to regularly identify and track existing, unanticipated, and emergent AI risks based on factors such as intended and actual performance in deployed contexts.
- **MEASURE 3.2** : Risk tracking approaches are considered for settings where AI risks are difficult to assess using currently available measurement techniques or where metrics are not yet available.
- **MEASURE 3.3** : Feedback processes for end users and impacted communities to report problems and appeal system outcomes are established and integrated into AI system evaluation metrics.

<!-- competency: measure-4-subcategories -->
## MEASURE 4 — Feedback About Efficacy of Measurement Gathered & Assessed {#glossary .weight-medium}

- **MEASURE 4.1** : Measurement approaches for identifying AI risks are connected to deployment context(s) and informed through consultation with domain experts and other end users. Approaches are documented.
- **MEASURE 4.2** : Measurement results regarding AI system trustworthiness in deployment context(s) and across the AI lifecycle are informed by input from domain experts and relevant AI actors to validate whether the system is performing consistently as intended. Results are documented.
- **MEASURE 4.3** : Measurable performance improvements or declines based on consultations with relevant AI actors, including affected communities, and field data about context-relevant risks and trustworthiness characteristics are identified and documented.

---

# MANAGE — Prioritize Risks and Act

<!-- competency: manage-purpose -->
## MANAGE — Overview {#key_takeaways .weight-high}

- **MANAGE** entails allocating risk resources to mapped and measured risks on a regular basis and as defined by the GOVERN function
- Risk treatment comprises plans to respond to, recover from, and communicate about incidents or events
- Contextual information gleaned from expert consultation and input from relevant AI actors — established in GOVERN and carried out in MAP — is utilized in MANAGE to decrease the likelihood of system failures and negative impacts
- Systematic documentation practices established in GOVERN and utilized in MAP and MEASURE bolster AI risk management efforts and increase transparency and accountability
- After MANAGE: plans for prioritizing risk and regular monitoring and improvement will be in place
- Risk response options: **mitigate, transfer, avoid, or accept**
- **MANAGE 1.1** is a go/no-go decision gate — determine whether the AI system achieves its intended purposes and whether development or deployment should proceed
- **4 categories, 13 subcategories total**: MANAGE 1 (4), MANAGE 2 (4), MANAGE 3 (2), MANAGE 4 (3)

<!-- competency: manage-1-subcategories -->
## MANAGE 1 — AI Risks Prioritized, Responded To & Managed {#glossary .weight-high}

- **MANAGE 1.1** : A determination is made as to whether the AI system achieves its intended purposes and stated objectives and whether its development or deployment should proceed.
- **MANAGE 1.2** : Treatment of documented AI risks is prioritized based on impact, likelihood, and available resources or methods.
- **MANAGE 1.3** : Responses to the AI risks deemed high priority, as identified by the MAP function, are developed, planned, and documented. Risk response options can include mitigating, transferring, avoiding, or accepting.
- **MANAGE 1.4** : Negative residual risks (defined as the sum of all unmitigated risks) to both downstream acquirers of AI systems and end users are documented.

<!-- competency: manage-2-subcategories -->
## MANAGE 2 — Strategies to Maximize Benefits & Minimize Negative Impacts {#glossary .weight-high}

- **MANAGE 2.1** : Resources required to manage AI risks are taken into account — along with viable non-AI alternative systems, approaches, or methods — to reduce the magnitude or likelihood of potential impacts.
- **MANAGE 2.2** : Mechanisms are in place and applied to sustain the value of deployed AI systems.
- **MANAGE 2.3** : Procedures are followed to respond to and recover from a previously unknown risk when it is identified.
- **MANAGE 2.4** : Mechanisms are in place and applied, and responsibilities are assigned and understood, to supersede, disengage, or deactivate AI systems that demonstrate performance or outcomes inconsistent with intended use.

<!-- competency: manage-3-subcategories -->
## MANAGE 3 — AI Risks & Benefits from Third-Party Entities Managed {#glossary .weight-medium}

- **MANAGE 3.1** : AI risks and benefits from third-party resources are regularly monitored, and risk controls are applied and documented.
- **MANAGE 3.2** : Pre-trained models which are used for development are monitored as part of AI system regular monitoring and maintenance.

<!-- competency: manage-4-subcategories -->
## MANAGE 4 — Risk Treatments, Response, Recovery & Communication Plans {#glossary .weight-high}

- **MANAGE 4.1** : Post-deployment AI system monitoring plans are implemented, including mechanisms for capturing and evaluating input from users and other relevant AI actors, appeal and override, decommissioning, incident response, recovery, and change management.
- **MANAGE 4.2** : Measurable activities for continual improvements are integrated into AI system updates and include regular engagement with interested parties, including relevant AI actors.
- **MANAGE 4.3** : Incidents and errors are communicated to relevant AI actors, including affected communities. Processes for tracking, responding to, and recovering from incidents and errors are followed and documented.

---

# Trustworthiness — Seven Characteristics of Trustworthy AI

<!-- competency: trust-overview -->
## Trustworthiness — Overview {#key_takeaways .weight-high}

- For AI systems to be trustworthy, they need to be responsive to a multiplicity of criteria that are of value to interested parties
- Trustworthiness is a social concept that ranges across a spectrum and is **only as strong as its weakest characteristic**
- Characteristics influence each other — tradeoffs between them are common (e.g., accuracy vs. privacy, transparency vs. security)
- Trustworthiness characteristics are **socio-technical in nature** — rooted in both technical aspects of AI and the social context in which AI systems are developed and deployed
- **Valid & Reliable** is the foundation — displayed as the platform under the other six characteristics; necessary condition for all trustworthiness
- **Accountable & Transparent** is a vertical cross-cutting characteristic — relates to and supports all other characteristics
- Understanding and treatment of characteristics depends on an **AI actor's particular role** within the lifecycle

<!-- competency: trust-seven-characteristics -->
## Seven Trustworthiness Characteristics {#glossary .weight-high}

- **Valid & Reliable** : The necessary foundation. Validation confirms that requirements for a specific intended use have been fulfilled. Reliability means the AI system performs as required without failure. The base condition shown as the platform under the other six characteristics — necessary for all other trustworthiness claims to hold.
- **Safe** : AI systems should not, under defined conditions, lead to a state in which human life, health, property, or the environment is endangered. Requires responsible design and deployment practices, clear information provision to enable responsible human use, and documentation of residual risk based on empirical evidence.
- **Secure & Resilient** : Resilient systems withstand unexpected adverse events or changes and degrade safely and gracefully. Secure systems prevent unauthorized access and use. Security includes resilience but also encompasses protocols to avoid, protect against, respond to, and recover from attacks.
- **Accountable & Transparent** : A cross-cutting, vertical characteristic. Transparency reflects the extent to which information about an AI system and its outputs is available to individuals interacting with it. Accountability presupposes transparency and relates to all other characteristics. The role of AI actors should be considered when seeking accountability for the outcomes of AI systems.
- **Explainable & Interpretable** : Explainability refers to a representation of the mechanisms underlying AI systems' operation. Interpretability refers to the meaning of AI systems' output in the context of their designed functional purpose. Together they help users gain deeper insights into the functionality and trustworthiness of the system. Transparency can answer "what happened"; explainability answers "how"; interpretability answers "why."
- **Privacy-Enhanced** : Privacy refers generally to the norms and practices that help to safeguard human autonomy, identity, and dignity — including freedom from intrusion, limiting observation, or individuals' agency to consent to disclosure or control of aspects of their identities. Privacy values should guide choices for AI system design, development, and deployment.
- **Fair — with Harmful Bias Managed** : Fairness in AI includes concerns for equality and equity by addressing issues such as harmful bias and discrimination. Standards of fairness can be complex and difficult to define because perceptions of fairness differ among cultures and may shift depending on application. Systems in which harmful biases are mitigated are not necessarily fair.

<!-- competency: trust-bias-categories -->
## Three Categories of AI Bias {#glossary .weight-medium}

- **Systemic bias** : Bias present in AI datasets, the organizational norms, practices, and processes across the AI lifecycle, and the broader society that uses AI systems. Can occur in the absence of prejudice, partiality, or discriminatory intent.
- **Computational and statistical bias** : Bias present in AI datasets and algorithmic processes, often stemming from systematic errors due to non-representative samples. Can occur in the absence of discriminatory intent.
- **Human-cognitive bias** : Bias that relates to how an individual or group perceives AI system information to make a decision or fill in missing information, or how humans think about purposes and functions of an AI system. Omnipresent in decision-making processes across the AI lifecycle including design, implementation, operation, and maintenance.
