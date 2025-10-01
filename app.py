def send_approval_email(first_name, last_name, email):
    full_name = f"{first_name} {last_name}"
    body_html = f"""
    <p>Dear {full_name},</p>

    <p>We are excited to inform you that your application has been approved — welcome on board!</p>

    <p><strong>About the Role</strong><br>
    As a chat moderator, your role is to engage with customers through our secure web-based platform. You will be replying to messages from users in English, keeping conversations fun, engaging, and creative. Many of these chats may be of a flirty or adult nature, so applicants must feel comfortable handling such conversations while maintaining professionalism and consistency.</p>

    <p>Your goal is simple: keep the conversation alive and enjoyable for the user while typing quickly and clearly.</p>

    <p><strong>Requirements</strong><br>
    To succeed as a moderator, you’ll need:</p>
    <ul>
        <li>Excellent written English and creativity in conversation.</li>
        <li>A computer or laptop (mobile is not supported).</li>
        <li>A reliable high-speed internet connection.</li>
        <li>A verified bank account or PayPal account for payments.</li>
    </ul>

    <p><strong>Work Hours</strong><br>
    You will have the freedom to choose your shifts, but please note that our busiest hours are at peak times of night. Weekend shifts are especially high in traffic and highly recommended for maximizing your earnings. We ask all moderators to commit to a minimum of 12 hours per week, booked in one-hour shifts.</p>

    <p><strong>Pay Structure</strong><br>
    Payment: €0.10 (10 Euro cents) per sent message.<br>
    Experienced moderators can type 80–100+ messages per hour, leading to competitive earnings depending on typing speed and commitment.<br>
    Payments are calculated from the 1st day of each month to the last day of the same month.<br>
    All payments are processed and paid on the 3rd day of the following month.<br>
    Payments are sent via PayPal, or direct bank transfer.</p>

    <p><strong>Training & Support</strong><br>
    Before starting, you’ll receive:</p>
    <ul>
        <li>A training manual covering everything you need to know.</li>
        <li>A one-on-one training session with an experienced team leader to guide you through the system and best practices.</li>
        <li>Ongoing support from our team whenever you need assistance.</li>
    </ul>

    <p><strong>Freelance Basis</strong><br>
    Please note, this is a freelance, self-employed role. This gives you flexibility while also requiring you to manage your own time and schedule responsibly.</p>

    <p><strong>Next Steps</strong><br>
    To proceed, you’ll need to complete a short test to demonstrate your level of English.<br>
    Simply click the link below to get started:<br>
    <a href="https://forms.gle/YvgBWxriV2hPfn82A">https://forms.gle/YvgBWxriV2hPfn82A</a><br>
    Once you have submitted your answers, our team will review them carefully. You will receive a response within 3 business days regarding the outcome and the next stage of onboarding.</p>

    <p>We are thrilled to have you with us and can’t wait to see you succeed as part of our ChatPlatform team.</p>

    <p>Welcome aboard, and let’s get started!</p>

    <p>Warm regards,<br>
    Work4U<br>
    Recruitment Team</p>
    """
    return send_email_html(email, "Your Application Has Been Approved", body_html)