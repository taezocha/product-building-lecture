
# Project Blueprint: Lotto Number Generator

## Overview

This project is a web-based lottery number generator. It provides users with a set of randomly generated numbers, typically for use in lottery drawings. The application is designed to be simple, user-friendly, and visually appealing.

## Features

*   **Number Generation:** Generates a set of 6 unique random numbers between 1 and 45.
*   **User Interface:** A clean and modern interface with a button to trigger the number generation and a clear display for the results.
*   **Responsive Design:** The layout adapts to different screen sizes, making it usable on both desktop and mobile devices.
*   **Theme Toggle:** Supports both Light and Dark modes with a persistent user preference.
*   **Partnership Inquiry Form:** A contact form powered by Formspree for handling business inquiries.
*   **Comments Section:** Interactive comment section powered by Disqus for user feedback and engagement.

## Design and Style

*   **Layout:** A centered, column-based layout that allows for multiple sections (Generator, Contact, and Comments).
*   **Colors:** A visually appealing color scheme using CSS variables for theme support.
*   **Typography:** Clear and readable fonts.
*   **Animation:** Subtle animations to enhance the user experience.

## Current Task

*   **Objective:** Integrate Disqus for comments.
*   **Steps:**
    1.  Add `<div id="disqus_thread"></div>` to `index.html` at the bottom of the page.
    2.  Add the Disqus configuration and initialization script to `main.js`.
    3.  Style the Disqus container in `style.css` to ensure proper spacing and alignment with the rest of the site.
    4.  Verify that the comment section loads correctly.
