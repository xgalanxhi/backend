# Archived Workflows

This directory contains old workflow files that have been replaced by the new modular workflow structure.

## Archived Files

- `dockerhub-build-push.yaml` - Old monolithic build workflow
- `build-test-push.yaml` - Old combined test and build workflow
- `deploy-backend-to-ecs.yaml` - Old deploy workflow

## New Workflow Structure

The workflows have been refactored into modular, composable workflows:

### Atomic Workflows (can be called independently):
- `test.yaml` - Run tests with Launchable integration
- `build.yaml` - Build and push Docker image
- `deploy.yaml` - Deploy to ECS

### Composite Workflows (call atomic workflows):
- `build-push.yaml` - Test → Build
- `build-push-deploy.yaml` - Test → Build → Deploy

## Migration

**Old workflow** → **New workflow**
- `dockerhub-build-push.yaml` → `build.yaml`
- `build-test-push.yaml` → `build-push.yaml`
- `deploy-backend-to-ecs.yaml` → `deploy.yaml`

These archived files can be safely deleted after confirming the new workflows work correctly.
