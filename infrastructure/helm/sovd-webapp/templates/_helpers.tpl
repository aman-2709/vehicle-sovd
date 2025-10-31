{{/*
Expand the name of the chart.
*/}}
{{- define "sovd-webapp.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "sovd-webapp.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "sovd-webapp.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "sovd-webapp.labels" -}}
helm.sh/chart: {{ include "sovd-webapp.chart" . }}
{{ include "sovd-webapp.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "sovd-webapp.selectorLabels" -}}
app.kubernetes.io/name: {{ include "sovd-webapp.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Backend labels
*/}}
{{- define "sovd-webapp.backend.labels" -}}
{{ include "sovd-webapp.labels" . }}
app.kubernetes.io/component: backend
app: backend
{{- end }}

{{/*
Backend selector labels
*/}}
{{- define "sovd-webapp.backend.selectorLabels" -}}
{{ include "sovd-webapp.selectorLabels" . }}
app.kubernetes.io/component: backend
app: backend
{{- end }}

{{/*
Frontend labels
*/}}
{{- define "sovd-webapp.frontend.labels" -}}
{{ include "sovd-webapp.labels" . }}
app.kubernetes.io/component: frontend
app: frontend
{{- end }}

{{/*
Frontend selector labels
*/}}
{{- define "sovd-webapp.frontend.selectorLabels" -}}
{{ include "sovd-webapp.selectorLabels" . }}
app.kubernetes.io/component: frontend
app: frontend
{{- end }}

{{/*
Vehicle Connector labels
*/}}
{{- define "sovd-webapp.vehicleConnector.labels" -}}
{{ include "sovd-webapp.labels" . }}
app.kubernetes.io/component: vehicle-connector
app: vehicle-connector
{{- end }}

{{/*
Vehicle Connector selector labels
*/}}
{{- define "sovd-webapp.vehicleConnector.selectorLabels" -}}
{{ include "sovd-webapp.selectorLabels" . }}
app.kubernetes.io/component: vehicle-connector
app: vehicle-connector
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "sovd-webapp.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "sovd-webapp.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Backend image name
*/}}
{{- define "sovd-webapp.backend.image" -}}
{{- $tag := .Values.backend.image.tag | default .Chart.AppVersion }}
{{- printf "%s:%s" .Values.backend.image.repository $tag }}
{{- end }}

{{/*
Frontend image name
*/}}
{{- define "sovd-webapp.frontend.image" -}}
{{- $tag := .Values.frontend.image.tag | default .Chart.AppVersion }}
{{- printf "%s:%s" .Values.frontend.image.repository $tag }}
{{- end }}

{{/*
Vehicle Connector image name
*/}}
{{- define "sovd-webapp.vehicleConnector.image" -}}
{{- $tag := .Values.vehicleConnector.image.tag | default .Chart.AppVersion }}
{{- printf "%s:%s" .Values.vehicleConnector.image.repository $tag }}
{{- end }}

{{/*
Database URL construction
*/}}
{{- define "sovd-webapp.databaseUrl" -}}
{{- printf "postgresql+asyncpg://%s:$(DATABASE_PASSWORD)@%s:%s/%s" .Values.config.database.user .Values.config.database.host .Values.config.database.port .Values.config.database.name }}
{{- end }}

{{/*
Redis URL construction
*/}}
{{- define "sovd-webapp.redisUrl" -}}
{{- if .Values.secrets.redisPassword }}
{{- printf "redis://:%s@%s:%s/%s" "$(REDIS_PASSWORD)" .Values.config.redis.host .Values.config.redis.port .Values.config.redis.db }}
{{- else }}
{{- printf "redis://%s:%s/%s" .Values.config.redis.host .Values.config.redis.port .Values.config.redis.db }}
{{- end }}
{{- end }}
