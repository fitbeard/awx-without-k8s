{{/*
Expand the name of the chart.
*/}}
{{- define "ap-gateway-operator.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "ap-gateway-operator.fullname" -}}
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
{{- define "ap-gateway-operator.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "ap-gateway-operator.labels" -}}
helm.sh/chart: {{ include "ap-gateway-operator.chart" . }}
{{ include "ap-gateway-operator.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "ap-gateway-operator.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ap-gateway-operator.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "ap-gateway-operator.serviceAccountName" -}}
{{- $default := (include "ap-gateway-operator.fullname" .) }}
{{- with .Values.serviceAccount }}
{{- if .create }}
{{- default $default .name }}
{{- else }}
{{- default "default" .name }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Cluster-scope flag: any watchNamespace value other than "release" or a single ns
that equals .Release.Namespace requires ClusterRole instead of Role.
We treat empty AND any comma-separated list as cluster-scope.
*/}}
{{- define "ap-gateway-operator.clusterScope" -}}
{{- $w := .Values.watchNamespace -}}
{{- if eq $w "" -}}true{{- else if contains "," $w -}}true{{- else -}}false{{- end -}}
{{- end }}
