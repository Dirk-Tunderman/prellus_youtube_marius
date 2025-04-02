import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useTranscriptContext } from "../context/TranscriptContext";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { useEffect } from "react";
import { Eraser } from "lucide-react";

// Form schema
const formSchema = z.object({
  url: z
    .string()
    .url("Please enter a valid YouTube URL")
    .min(1, "URL is required"),
  title: z.string().optional(),
  duration: z.string().optional(),
});

export function TranscriptForm() {
  const {
    url,
    setUrl,
    title,
    setTitle,
    duration,
    setDuration,
    isProcessing,
    resetForm,
  } = useTranscriptContext();

  // Define form
  const form = useForm({
    resolver: zodResolver(formSchema),
    defaultValues: {
      url: url,
      title: title,
      duration: duration.toString(),
    },
  });

  // Update form values when context values change
  useEffect(() => {
    form.setValue("url", url);
    form.setValue("title", title);
    form.setValue("duration", duration.toString());
  }, [form, url, title, duration]);

  // Update context values when form values change
  const handleFieldChange = (field, value) => {
    if (field === "url") setUrl(value);
    if (field === "title") setTitle(value);
    if (field === "duration") setDuration(value);
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle>Video Information</CardTitle>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            resetForm();
            form.reset({
              url: "",
              title: "",
              duration: "",
            });
          }}
          disabled={isProcessing}
        >
          <Eraser className="mr-2 h-4 w-4" />
          Clear Form
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        <Form {...form}>
          <div className="space-y-4">
            <FormField
              control={form.control}
              name="url"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>YouTube URL</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="https://www.youtube.com/watch?v=..."
                      disabled={isProcessing}
                      {...field}
                      onChange={(e) => {
                        field.onChange(e);
                        handleFieldChange("url", e.target.value);
                      }}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="title"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Title (Optional)</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="Enter a title for this transcript"
                      disabled={isProcessing}
                      {...field}
                      onChange={(e) => {
                        field.onChange(e);
                        handleFieldChange("title", e.target.value);
                      }}
                    />
                  </FormControl>
                  <FormDescription>
                    If left blank, a title will be generated from the video ID
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="duration"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Duration (minutes)</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      max="180"
                      disabled={isProcessing}
                      {...field}
                      onChange={(e) => {
                        field.onChange(e);
                        handleFieldChange("duration", e.target.value);
                      }}
                    />
                  </FormControl>
                  <FormDescription>
                    Maximum length of the video to process (up to 180 minutes,
                    leave empty for no limit)
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
        </Form>
      </CardContent>
    </Card>
  );
}
