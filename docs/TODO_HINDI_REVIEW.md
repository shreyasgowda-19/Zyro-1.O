# Hindi Localization Review Checklist (TODO_HINDI_REVIEW.md)

This document tracks all translated Hindi strings across the PayGuard 360 platform requiring validation by native Hindi speakers and legal/fintech domain experts.

| Key | Current Hindi String | Context / Parameters | Review Status | Notes |
|---|---|---|---|---|
| `app.demo_mode` | डेमो मोड — कोई वास्तविक धन हस्तांतरण नहीं | Persistent banner | Pending | Clear and prominent warning |
| `app.credential_warning` | पेगार्ड 360 कभी भी आपका पिन, ओटीपी या पासवर्ड नहीं मांगेगा। | Security notice | Pending | Emphasizes credential protection |
| `risk.reason.R1` | असामान्य भुगतान राशि: आपके हाल के औसत {avg_paise} से {multiple_x10} गुना अधिक ({sample_size} लेनदेन मूल्यांकित)। | Parameterized risk explanation | Pending | Verify mathematical phrasing |
| `risk.reason.R3` | असामान्य समय: भुगतान {local_hour}:{local_minute} IST पर शुरू किया गया (रात की खिड़की 00:00-05:00)। | Night window explanation | Pending | Phrasing for "night window" |
| `risk.reason.R5` | अपरिचित उपकरण या स्थान: भुगतान अपरिचित {signals} से शुरू किया गया। | Device / city signals | Pending | Phrasing for synthetic signals |
| `risk.reason.R7` | संदिग्ध पैटर्न: लेनदेन की राशि गोल सीमा के निकट है या 24 घंटे में दोहराया गया समान भुगतान है। | Threshold avoidance / repeat | Pending | Technical threshold terminology |
| `risk.reason.R8` | भुगतान विवरण में ज्ञात सामाजिक धोखाधड़ी से मेल खाने वाले संदिग्ध शब्द मिले। | Social engineering lure | Pending | Social engineering phrasing |
| `risk.reason.R9` | शेष राशि का बड़ा हिस्सा: लेनदेन आपके उपलब्ध शेष का {share_pct}% उपयोग करता है ({available_paise} में से {amount_paise})। | Balance drain | Pending | Percentage and balance context |
| `risk.reason.R10` | असत्यापित कलेक्ट अनुरोध: भुगतान अनुरोध किसी अज्ञात पक्ष द्वारा शुरू किया गया था। | Collect request trap | Pending | UPI collect terminology |
| `pay.checklist_1..5` | भुगतान से पहले सुरक्षा चेकलिस्ट (5 प्रश्न) | Interactive safety checklist | Pending | Ensure colloquial understanding |
| `scam_advice.report_1930` | संदिग्ध वित्तीय साइबर अपराध की तुरंत राष्ट्रीय हेल्पलाइन 1930 या cybercrime.gov.in पर रिपोर्ट करें। | Regulatory advisory | Verified | Official MHA guidance wording |
| `scam_advice.never_share_credentials` | याद रखें: बैंक अधिकारी और वास्तविक व्यापारी कभी भी पिन, ओटीपी या सीवीवी नहीं मांगेंगे। | Security principle | Verified | Matches RBI financial literacy campaigns |

*Last updated: Phase 4 Verification*
