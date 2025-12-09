# Vercel Deployment for Codegen Documentation

This document explains how to set up Vercel deployments for the Codegen documentation site.

## PR Deployments

The repository is configured to automatically deploy PR previews to Vercel when changes are made to the `docs/` directory.

### Setup Instructions

To enable PR deployments to Vercel, follow these steps:

1. **Create a Vercel Project**:

   - Go to [Vercel](https://vercel.com) and create a new project
   - Import the `codegen` repository
   - Configure the project with the following settings:
     - Framework Preset: Other
     - Build Command: `echo 'Mintlify docs deployment'`
     - Output Directory: `docs`

1. **Configure GitHub Secrets**:

   - In the GitHub repository settings, add the following secrets:
     - `VERCEL_TOKEN`: Your Vercel API token (create one in Vercel account settings)
     - `VERCEL_ORG_ID`: Your Vercel organization ID (found in Vercel project settings)
     - `VERCEL_PROJECT_ID`: Your Vercel project ID (found in Vercel project settings)

1. **Mintlify Integration**:

   - Ensure your Mintlify account is connected to the Vercel project
   - Mintlify will handle the actual documentation rendering

## How It Works

When a PR is opened or updated that includes changes to the `docs/` directory:

1. The GitHub workflow `.github/workflows/vercel-pr-deployment.yml` is triggered
1. The workflow deploys the documentation to Vercel
1. A comment is added to the PR with a link to the preview deployment
1. You can view the documentation preview to verify changes before merging

## Production Deployment

The production deployment is handled separately and is triggered when changes are merged to the main branch.

## Troubleshooting

If you encounter issues with the Vercel deployment:

1. Check that all required secrets are properly configured
1. Verify that the Vercel project settings match the configuration in `vercel.json`
1. Ensure the Mintlify integration is properly set up
1. Check the GitHub Actions logs for any error messages
