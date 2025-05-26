{{- define "project.name" }}
{{- if .Values.projectNameOverride }}
{{- .Values.projectNameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{ .Chart.Name }}
{{- end }}
{{- end }}